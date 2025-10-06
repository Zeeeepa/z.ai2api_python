#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Image and Video Generation Endpoints
OpenAI-compatible API endpoints for Qwen image/video generation
"""

from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.utils.logger import get_logger
from app.providers import get_provider_router

logger = get_logger()
router = APIRouter()


# Request models

class ImageGenerationRequest(BaseModel):
    """OpenAI-compatible image generation request"""
    prompt: str = Field(..., description="Text description of desired image")
    model: Optional[str] = Field(default="qwen-max-image", description="Model to use")
    n: Optional[int] = Field(default=1, description="Number of images (1-4)")
    size: Optional[str] = Field(default="1024x1024", description="Image size")
    response_format: Optional[str] = Field(default="url", description="Response format (url or b64_json)")


class ImageEditRequest(BaseModel):
    """OpenAI-compatible image editing request"""
    image: str = Field(..., description="Base64 encoded image or URL")
    prompt: str = Field(..., description="Edit instructions")
    mask: Optional[str] = Field(default=None, description="Base64 encoded mask image")
    model: Optional[str] = Field(default="qwen-max-image_edit", description="Model to use")
    n: Optional[int] = Field(default=1, description="Number of images")
    size: Optional[str] = Field(default="1024x1024", description="Image size")


class VideoGenerationRequest(BaseModel):
    """Video generation request"""
    prompt: str = Field(..., description="Text description of desired video")
    model: Optional[str] = Field(default="qwen-max-video", description="Model to use")
    duration: Optional[int] = Field(default=5, description="Video duration in seconds")
    size: Optional[str] = Field(default="1920x1080", description="Video resolution")


# Endpoints

@router.post("/v1/images/generations")
async def generate_images(request: ImageGenerationRequest, authorization: str = Header(...)):
    """
    Generate images from text prompts
    
    OpenAI-compatible endpoint for text-to-image generation
    """
    logger.info(f"🎨 Image generation request: '{request.prompt[:50]}...' size={request.size}")
    
    try:
        # Validate auth
        if not settings.SKIP_AUTH_TOKEN:
            if not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
            
            api_key = authorization[7:]
            if api_key != settings.AUTH_TOKEN:
                raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Get provider
        provider_router = get_provider_router()
        provider = provider_router._get_provider_for_model(request.model or "qwen-max-image")
        
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider not found for model: {request.model}")
        
        # Generate image
        result = await provider.generate_image(
            prompt=request.prompt,
            model=request.model or "qwen-max-image",
            size=request.size,
            n=request.n
        )
        
        logger.info("✅ Image generation successful")
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation error: {str(e)}")


@router.post("/v1/images/edits")
async def edit_images(request: ImageEditRequest, authorization: str = Header(...)):
    """
    Edit images based on text instructions
    
    OpenAI-compatible endpoint for image editing
    """
    logger.info(f"🎨 Image edit request: '{request.prompt[:50]}...'")
    
    try:
        # Validate auth
        if not settings.SKIP_AUTH_TOKEN:
            if not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
            
            api_key = authorization[7:]
            if api_key != settings.AUTH_TOKEN:
                raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Get provider
        provider_router = get_provider_router()
        provider = provider_router._get_provider_for_model(request.model or "qwen-max-image_edit")
        
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider not found for model: {request.model}")
        
        # Edit image
        result = await provider.edit_image(
            image=request.image,
            prompt=request.prompt,
            mask=request.mask,
            model=request.model or "qwen-max-image_edit",
            size=request.size,
            n=request.n
        )
        
        logger.info("✅ Image editing successful")
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Image editing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image editing error: {str(e)}")


@router.post("/v1/videos/generations")
async def generate_videos(request: VideoGenerationRequest, authorization: str = Header(...)):
    """
    Generate videos from text prompts
    
    Qwen-specific endpoint for text-to-video generation
    """
    logger.info(f"🎬 Video generation request: '{request.prompt[:50]}...' duration={request.duration}s")
    
    try:
        # Validate auth
        if not settings.SKIP_AUTH_TOKEN:
            if not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
            
            api_key = authorization[7:]
            if api_key != settings.AUTH_TOKEN:
                raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Get provider
        provider_router = get_provider_router()
        provider = provider_router._get_provider_for_model(request.model or "qwen-max-video")
        
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider not found for model: {request.model}")
        
        # Generate video
        result = await provider.generate_video(
            prompt=request.prompt,
            model=request.model or "qwen-max-video",
            duration=request.duration,
            size=request.size
        )
        
        logger.info("✅ Video generation successful")
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Video generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video generation error: {str(e)}")


class DeepResearchRequest(BaseModel):
    """Deep research request"""
    query: str = Field(..., description="Research question")
    model: Optional[str] = Field(default="qwen-max-deep-research", description="Model to use")
    max_iterations: Optional[int] = Field(default=3, description="Maximum research iterations")


@router.post("/v1/research/deep")
async def deep_research(request: DeepResearchRequest, authorization: str = Header(...)):
    """
    Perform deep research on a query
    
    Qwen-specific endpoint for comprehensive research with citations
    """
    logger.info(f"🔬 Deep research request: '{request.query[:50]}...' max_iterations={request.max_iterations}")
    
    try:
        # Validate auth
        if not settings.SKIP_AUTH_TOKEN:
            if not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
            
            api_key = authorization[7:]
            if api_key != settings.AUTH_TOKEN:
                raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Get provider
        provider_router = get_provider_router()
        provider = provider_router._get_provider_for_model(request.model or "qwen-max-deep-research")
        
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider not found for model: {request.model}")
        
        # Perform deep research
        result = await provider.deep_research(
            query=request.query,
            model=request.model or "qwen-max-deep-research",
            max_iterations=request.max_iterations
        )
        
        logger.info("✅ Deep research successful")
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Deep research failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deep research error: {str(e)}")
