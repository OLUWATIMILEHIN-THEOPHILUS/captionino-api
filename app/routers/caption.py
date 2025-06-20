# Caption generation logic here.
from fastapi import APIRouter, status, UploadFile, File, Depends, HTTPException, Request
from .. import schemas, oauth2, storage, models, utils, free_trials
from ..database import get_db
from sqlalchemy.orm import Session
from ..config import settings
import replicate
from starlette.responses import JSONResponse
from uuid import UUID
from fastapi.encoders import jsonable_encoder

router = APIRouter(
    prefix="/caption",
    tags=["Caption"]
)

replicate_client = replicate.Client(api_token=settings.replicate_api_token)

@router.get("/captions", status_code=status.HTTP_200_OK, response_model=dict)
async def get_user_captions(db: Session = Depends(get_db),
                           current_user: int = Depends(oauth2.get_all_current_user)):
    
    caption_query = db.query(models.Caption).filter(models.Caption.user_id == current_user.id)
    if caption_query:
        captions = caption_query.all()
        return {
            "message": "Your captions",
            "captions": jsonable_encoder(schemas.CaptionsResponse(count=len(captions), captions=captions))
        }
    else:
        return {
            "message": "You have not generated any caption yet."
        }

@router.get("/caption/{id}", status_code=status.HTTP_200_OK, response_model=dict)
async def get_caption(id: UUID, db: Session = Depends(get_db),
                           current_user: int = Depends(oauth2.get_all_current_user)):
    
    caption_query = db.query(models.Caption).filter(models.Caption.id == id)
    caption = caption_query.first()
    if caption:
        if caption.user_id==current_user.id:
            return {
                "message": "Caption",
                "caption": jsonable_encoder(schemas.CaptionResponse.model_validate(caption))
            }
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"You can only view your caption")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Caption not found")

@router.post("/generate-caption", status_code=status.HTTP_201_CREATED, response_model=dict)
async def generate_caption(c_image: UploadFile = File(...), 
                           c_data: str = Depends(schemas.CaptionRequest.as_form),
                           db: Session = Depends(get_db),
                           current_user: int = Depends(oauth2.get_all_current_user)):
    # subscription logic
    has_active_sub = utils.check_active_subscription(user_id=current_user.id, db=db)
    # print(f"has_active_sub: {has_active_sub}")

    # daily limit logic
    reached_daily_limit = utils.check_daily_limit_reached(user_id=current_user.id, has_active_sub=has_active_sub, db=db)
    # print(f"reached_daily_limit: {reached_daily_limit}")

    # free trials logic
    has_trials_left = free_trials.check_free_trial_eligibility(user_id=current_user.id, db=db)
    # print(f"has_trials_left: {has_trials_left}")

    if not has_active_sub and not has_trials_left:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"No active subscription or free trial. Please subscribe to continue generating caption.")

    if has_active_sub and reached_daily_limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Daily limit reached. Please try again tomorrow.")

    # Upload to temp storage first;
    temp_image_url, image_key = await storage.upload_temp_image(c_image)

    # Replicate caption generation prompts.
    if c_data.c_type == "social media":
        c_prompt = (
            "Instruction: You are a modern social media caption writer with a poetic and vibey style. "
            "Write a short, aesthetic caption using stylized sentence fragments but avoids storytelling or full sentences."
            "Do not start with 'a', 'this is a' or other generic starters."
            "Use evocative, fragment-style language instead of full descriptions."
            # "Avoid using 'a', 'this', 'he', 'his', 'it', or full sentences or other generic starters or phrasing like 'as he...', 'making it...'. "
            "Think like an Instagram or TikTok user dropping a cool caption — punchy, vibey, poetic."
            # "Tone: poetic, confident, stylish, vibey — like something someone would actually post on Instagram or TikTok. "
            "Tone: confident, playful, stylish, and relatable. "
            "Format: sentence fragments, aesthetic lines, or even poetic stanzas. "
            "Include commas and punctuation for rhythm. Do not write more than 4-5 lines. "
            "Examples: 'Feathered elegance, no apologies. Swagger turned up.' or 'Dapper duck and bow tie swagger. Waddling in style. 'Not your average duck.''"
        )

    elif c_data.c_type == "product description":
        c_prompt = (
            "Instruction: You are a product caption specialist with a knack for making items sound desirable and stylish. "
            "Write a caption, not too long, in aesthetic fragments — avoid full sentences. "
            # "No use of 'a', 'this', 'it', or generic phrases. "
            "Keep it persuasive but informal. Use sentence fragments if they add flair. "
            # "Focus on mood, features, or standout details in a catchy, minimal way but somehow descriptive. "
            "Highlight visual appeal, feel, or benefits of the product without sounding robotic. "
            "Tone: minimal, stylish, modern, and aspirational. "
            "Avoid: generic phrases, hard sells, or long sentences."
            # "Use commas or short punchy lines for rhythm. "
            "Examples: 'Crafted to stand out. Minimal, not basic....' or 'Clean lines, loud presence.'"
        )

    elif c_data.c_type == "travel":
        c_prompt = (
            "Instruction: You are a poetic travel influencer writing vibey location captions. "
            # "Write a caption, not too long, in aesthetic fragments — not full sentences or diary-style writing. "
            "Focus on mood, emotion, and vibes over full storytelling. "
            "Use sentence fragments or poetic lines. "
            "Avoid phrases like 'this place', 'I went to'. No narrative or passive voice or listicle-style narration."
            "Tone: dreamy, inspiring, visual. "
            "Capture atmosphere, mood, and scenery in punchy lines with commas or stops. "
            "Examples: 'Golden skies, wind-kissed cliffs and view of comforting nature.' or 'Wander mode, always on.'"
        )

    elif c_data.c_type == "food":
        c_prompt = (
            "Instruction: You are a food blogger writing fun, stylish captions for dishes. "
            # "Use sentence fragments only — not reviews, not stories. "
            "Use sensory, playful language to describe the dish's vibe, flavor, or aesthetic. "
            "Avoid full recipe-like descriptions. Use short, punchy fragments. "
            "Avoid words like 'this', 'a dish', 'it’s made of'. Highlight vibe, flavor, experience. "
            "Tone: indulgent, witty, food-porn-esque, playful, delicious, visual. Use short stanzas or fragments, max 4-5 lines. "
            "Examples: 'Spice meets sauce. Fork can’t wait and the mouth with no patience. One bite, and you're in love.' or 'Crunch, drizzle, gone.'"
        )

    # elif c_data.c_type == "receipt":
    #     c_prompt = (
    #         "Instruction: You are an intelligent OCR agent specialized in analyzing receipts. "
    #         "If the image is clearly a receipt, extract and return structured JSON with: 'merchant', 'date', 'items' (list of name, qty, price), 'subtotal', 'tax', and 'total'. "
    #         "If the image is not a clear receipt, generate a short, poetic-style caption about daily expenses or spending vibes. "
    #         "Use sentence fragments only. Avoid 'this', 'it', or narrative lines. "
    #         "Examples: 'Grocery vibes. Little wins, big bites.' or 'Receipts stack, stories untold.'"
    #         "Respond in plain text, not markdown or code block format."
    #     )

    # Optional Instruction
    if c_data.c_instruction:
        c_prompt += f" {c_data.c_instruction}"



                                            # USING OUTPUT
    # input = {
    # "image": temp_image_url,
    # "prompt": c_prompt
    # }

    # output = replicate_client.run(
    #     "yorickvp/llava-13b:80537f9eead1a5bfa72d5ac6ea6414379be41d4d4f6679fd776e9535d1eb58bb",
    #     input=input
    # )
    # output_text = "".join(output)

    # result = {
    #     "c_image": temp_image_url,
    #     "c_text": output_text,
    # }

    # if not output:
    #     storage.delete_image(image_key)
    #     print(f"image deleted as caption failed: {image_key}")
    #     raise HTTPException(status_code=500, detail="Caption generation failed!")

    # return JSONResponse(content={
    #     "caption": result
    #     'image_key': image_key,
    #     'c_type': c_data.c_type,
    #     'has_active_sub': has_active_sub,
    #     'has_trials_left': has_trials_left,
    #     'reached_daily_limit': reached_daily_limit
    # })


                                            # USING STREAMING
    input = {
    "image": temp_image_url,
    "prompt": c_prompt
    }
    
    prediction = replicate_client.predictions.create(
        version="80537f9eead1a5bfa72d5ac6ea6414379be41d4d4f6679fd776e9535d1eb58bb",
        input=input,
        stream=True,
    )

    if prediction is None or not hasattr(prediction, 'urls'):
        storage.delete_image(image_key)
        # print(f"image deleted as caption failed: {image_key}")
        raise HTTPException(status_code=500, detail="Caption generation failed!")

    return JSONResponse(content={
        'url': prediction.urls['stream'],
        # 'cancel': prediction.urls['cancel'],
        'image_key': image_key,
        'c_type': c_data.c_type,
        'has_active_sub': has_active_sub,
        'has_trials_left': has_trials_left,
        'reached_daily_limit': reached_daily_limit
    })


@router.post("/save-caption", status_code=status.HTTP_201_CREATED, response_model=dict)
async def save_caption(c_data: schemas.CaptionSaveRequest, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_all_current_user)):
    
    # Don't save or update quota if caption text is empty.
    if not c_data.c_text.strip():
        storage.delete_image(image_key=c_data.image_key)
        # print(f"Caption was empty, image deleted: {c_data.image_key}")
        raise HTTPException(status_code=400, detail="Caption is empty, nothing was saved.")

    # only if has_active_sub, move the image into a permanent folder, and save the url into the database.
    if c_data.has_active_sub:
        # print(f"c_data_has_active_sub: {c_data.has_active_sub}")
        perm_image_url = await storage.move_image_permanently(image_key=c_data.image_key, user_id=current_user.id)
        # print(f"image has been moved to permanent directory: {c_data.image_key}")

        new_caption = models.Caption(user_id=current_user.id, c_text=c_data.c_text, image_url=perm_image_url, c_type=c_data.c_type)

        db.add(new_caption)
        db.commit()
        db.refresh(new_caption)

        # Increament daily usage after caption was successful and saved.
        utils.increment_daily_usage(user_id=current_user.id, used_subscription=True, reached_daily_limit=c_data.reached_daily_limit, db=db)
        
        # Get updated daily limit and send to the frontend.
        updated_reached_daily_limit = utils.check_daily_limit_reached(user_id=current_user.id, has_active_sub=c_data.has_active_sub, db=db)

        return JSONResponse(content={
            "message": "Caption saved successfully!",
            "caption": jsonable_encoder(schemas.CaptionResponse.model_validate(new_caption)),
            'updated_reached_daily_limit': updated_reached_daily_limit 
        })

    else:
        storage.delete_image(image_key=c_data.image_key)
        # print(f"image deleted after caption was generated for unsubscribed user: {c_data.image_key}")

        # Decreament free trials after caption was successful and saved.
        free_trials.decrement_trials_left(user_id=current_user.id, has_active_sub=c_data.has_active_sub, db=db)

        # Get updated free trials and send to the frontend.
        updated_has_trials_left = free_trials.check_free_trial_eligibility(user_id=current_user.id, db=db)

        return JSONResponse(content={
            "message": "Caption not saved. No active subscription.",
            'updated_has_trials_left': updated_has_trials_left, 
            'status': status.HTTP_402_PAYMENT_REQUIRED
        })