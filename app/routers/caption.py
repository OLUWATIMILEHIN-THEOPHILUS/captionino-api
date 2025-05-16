# Caption generation logic here.
from fastapi import APIRouter, status, UploadFile, File, Depends, HTTPException, Request
from .. import schemas, oauth2, storage, models, utils, free_trials
from ..database import get_db
from sqlalchemy.orm import Session
from ..config import settings
import replicate
from starlette.responses import JSONResponse
from uuid import UUID

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
            "captions": schemas.CaptionsResponse(count=len(captions), captions=captions)
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
                "caption": schemas.CaptionResponse.model_validate(caption)
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
    print(f"has_active_sub: {has_active_sub}")

    # daily limit logic
    reached_daily_limit = utils.check_daily_limit_reached(user_id=current_user.id, has_active_sub=has_active_sub, db=db)
    print(f"reached_daily_limit: {reached_daily_limit}")

    # free trials logic
    has_trials_left = free_trials.check_free_trial_eligibility(user_id=current_user.id, db=db)
    print(f"has_trials_left: {has_trials_left}")

    if not has_active_sub and not has_trials_left:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"No active subscription or free trial. Please subscribe to continue generating caption.")

    if has_active_sub and reached_daily_limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Daily limit reached. Please try again tomorrow.")

    # Upload to temp storage first;
    temp_image_url, image_key = await storage.upload_temp_image(c_image)

    # Replicate caption generation 
    if c_data.c_type == "social media":
        c_prompt = "generate a caption for this image, assuming it is for a social media post, e.g instagram post, facebook post, whatsapp status, twitter  e.t.c. make it short and poetic if need be."
    elif c_data.c_type == "product description":
        c_prompt = "generate a caption for this image, assuming it is for a product description. make it convincing and descriptive."
    elif c_data.c_type == "travel":
        c_prompt = "generate a caption for this image, assuming it is relating to travel. include location and notable place detected if need be."
    elif c_data.c_type == "food":
        c_prompt = "generate a caption for this image, assuming it is relating to food. include food description, health benefits, history e.t.c. if need be."
    # elif c_data.c_type == "receipt":
    #     c_prompt = "extract and return a structerd texts and figures from the image if it is a receipt, else generate a caption for it relating to receipt."

    if c_data.c_instruction:
        c_prompt += f" {c_data.c_instruction}"

                                            # OUTPUT
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

    # only if the user has active subscription, move the image into a permanent folder, and save the url into the database
    # if has_active_sub:
    #     perm_image_url = await storage.move_image_permanently(image_key=image_key, user_id=current_user.id)
    #     print(f"image has been moved to permanent directory: {image_key}")

    #     new_caption = models.Caption(user_id=current_user.id, text=result["c_text"], image_url=perm_image_url) #type=type

    #     db.add(new_caption)
    #     db.commit()
    #     db.refresh(new_caption)
        
    #     return {
    #         "message": "Caption generated successfully!",
    #         "caption": result,
    #         "saved_caption": schemas.CaptionResponse.model_validate(new_caption)
    #     }
    # else:
    #     storage.delete_image(image_key=image_key)
    #     print(f"image deleted after caption was generated for unsubscribed user: {image_key}")
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"No active subscription or free trial. Please subscribe to save your caption.")

    
    # return {
    #     "message": "Caption generated successfully!",
    #     "caption": result
    # }


                                            # STREAMING
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
        print(f"image deleted as caption failed: {image_key}")
        raise HTTPException(status_code=500, detail="Caption generation failed!")
    
    # Direct
    if has_active_sub:
        utils.increment_daily_usage(user_id=current_user.id, used_subscription=True, reached_daily_limit=reached_daily_limit, db=db)
    else:
        free_trials.decrement_trials_left(user_id=current_user.id, has_active_sub=has_active_sub, db=db)

    # Bool
    # used_free_trial = free_trials.decrement_trials_left(current_user.id, has_active_sub, db)

    # if not used_free_trial:
    #     utils.increment_daily_usage(current_user.id, used_subscription=True)

    updated_has_trials_left = free_trials.check_free_trial_eligibility(user_id=current_user.id, db=db)
    updated_reached_daily_limit = utils.check_daily_limit_reached(user_id=current_user.id, has_active_sub=has_active_sub, db=db)

    return JSONResponse(content={
        'url': prediction.urls['stream'],
        'image_key': image_key,
        'c_type': c_data.c_type,
        'has_active_sub': has_active_sub,
        'has_trials_left': has_trials_left,
        'updated_has_trials_left': updated_has_trials_left,
        'updated_reached_daily_limit': updated_reached_daily_limit 
    })


@router.post("/save-caption", status_code=status.HTTP_201_CREATED, response_model=dict)
async def save_caption(c_data: schemas.CaptionSaveRequest, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_all_current_user)):
    

    # only if has_active_sub, move the image into a permanent folder, and save the url into the database.
    if c_data.has_active_sub:
        print(f"c_data_has_active_sub: {c_data.has_active_sub}")
        perm_image_url = await storage.move_image_permanently(image_key=c_data.image_key, user_id=current_user.id)
        print(f"image has been moved to permanent directory: {c_data.image_key}")

        new_caption = models.Caption(user_id=current_user.id, c_text=c_data.c_text, image_url=perm_image_url, c_type=c_data.c_type)

        db.add(new_caption)
        db.commit()
        db.refresh(new_caption)
        
        return {
            "message": "Caption saved successfully!",
            "caption": schemas.CaptionResponse.model_validate(new_caption)
        }
    else:
        storage.delete_image(image_key=c_data.image_key)
        print(f"image deleted after caption was generated for unsubscribed user: {c_data.image_key}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"No active subscription. Please subscribe to save your caption.")