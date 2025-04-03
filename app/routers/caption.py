# Caption generation logic here.
from fastapi import APIRouter, status, UploadFile, File, Depends, HTTPException, Request
from .. import schemas, oauth2, storage, models, utils
from ..database import get_db
from sqlalchemy.orm import Session
from ..config import settings
import replicate
from starlette.responses import JSONResponse

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
            "message": "You have not generated any caption yet"
        }


@router.post("/generate-caption", status_code=status.HTTP_201_CREATED, response_model=dict)
async def generate_caption(c_image: UploadFile = File(...), 
                           c_data: str = Depends(schemas.CaptionRequest.as_form),
                           db: Session = Depends(get_db),
                           current_user: int = Depends(oauth2.get_all_current_user)):
    
    has_credits = False 
    user = db.query(models.User).filter_by(id=current_user.id).first()
    if user.email == "oluwatimilehintheophilus@gmail.com":
        has_credits = True

    if not has_credits:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"You do not have an active subscription or credits, please subscribe to continue generating captions!")

    # Upload to temp storage first;

    temp_image_url, image_key = await storage.upload_temp_image(c_image)

    # Replicate caption generation 

    c_prompt = f"Generate a caption from this image, assuming it is for {c_data.c_type}."
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

    # only if the user has credits/subscription, move the image into a permanent folder, and save the url into the database
    # if has_credits:
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
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"You do not have an active subscription or credits, please subscribe to continue generating captions!")

    
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

    return JSONResponse(content={
        'url': prediction.urls['stream'],
        'image_key': image_key,
        'c_type': c_data.c_type,
        'has_credits': has_credits
    })


@router.post("/save-caption", status_code=status.HTTP_201_CREATED, response_model=dict)
async def save_caption(c_data: schemas.CaptionSaveRequest, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_all_current_user)):
    

    # only if has_credits/subscription, move the image into a permanent folder, and save the url into the database
    if c_data.has_credits:
        perm_image_url = await storage.move_image_permanently(image_key=c_data.image_key, user_id=current_user.id)
        print(f"image has been moved to permanent directory: {c_data.image_key}")

        new_caption = models.Caption(user_id=current_user.id, c_text=c_data.c_text, image_url=perm_image_url, c_type=c_data.c_type)

        db.add(new_caption)
        db.commit()
        db.refresh(new_caption)
        
        return {
            "message": "Caption generated successfully!",
            "caption": schemas.CaptionResponse.model_validate(new_caption)
        }
    else:
        storage.delete_image(image_key=c_data.image_key)
        print(f"image deleted after caption was generated for unsubscribed user: {c_data.image_key}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You do not have an active subscription or credits, please subscribe to continue generating captions!")