from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
import os
import tempfile
import numpy as np
from app.services.handwriting import Hand

router = APIRouter(
    prefix="/handwriting",
    tags=["handwriting"],
)

# Initialize the handwriting model
hand = Hand()


@router.post("/generate")
async def generate_handwriting(
    lines: List[str] = Body(...),
    biases: Optional[List[float]] = Body(None),
    styles: Optional[List[int]] = Body(None),
    stroke_colors: Optional[List[str]] = Body(None),
    stroke_widths: Optional[List[int]] = Body(None),
):
    """
    Generate handwriting from the provided text lines
    """
    try:
        # Create a temporary file for the SVG output
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as temp_file:
            output_path = temp_file.name

        # Generate the handwriting
        hand.write(
            filename=output_path,
            lines=lines,
            biases=biases,
            styles=styles,
            stroke_colors=stroke_colors,
            stroke_widths=stroke_widths,
        )

        # Read the generated SVG file
        with open(output_path, "r") as f:
            svg_content = f.read()

        # Clean up the temporary file
        os.unlink(output_path)

        return {
            "status": "success",
            "svg_content": svg_content,
            "message": "Handwriting generated successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating handwriting: {str(e)}"
        )


@router.get("/styles")
async def list_styles():
    """
    List all available handwriting styles
    """
    try:
        # Get style files from the styles directory
        style_files = os.listdir("styles")

        # Extract unique style IDs
        style_ids = set()
        for file in style_files:
            if file.startswith("style-") and file.endswith(
                ("-chars.npy", "-strokes.npy")
            ):
                # Extract the style ID from filenames like "style-0-chars.npy"
                style_id = int(file.split("-")[1].split("-")[0])
                style_ids.add(style_id)

        # Sort the style IDs
        styles_list = sorted(list(style_ids))

        return {
            "status": "success",
            "styles": styles_list,
            "count": len(styles_list),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing styles: {str(e)}")


@router.get("/styles/{style_id}")
async def get_style(style_id: int):
    """
    Get information about a specific handwriting style
    """
    try:
        # Check if style files exist
        chars_path = f"styles/style-{style_id}-chars.npy"
        strokes_path = f"styles/style-{style_id}-strokes.npy"

        if not (os.path.exists(chars_path) and os.path.exists(strokes_path)):
            raise HTTPException(status_code=404, detail=f"Style {style_id} not found")

        # Load the style data
        try:
            chars_data = np.load(chars_path).tobytes().decode("utf-8")

            # Get some metadata about the style
            strokes_data = np.load(strokes_path)
            stroke_count = len(strokes_data)
            sample_text = chars_data.strip()

            return {
                "status": "success",
                "style_id": style_id,
                "stroke_count": stroke_count,
                "sample_text": sample_text,
                "preview": generate_preview(style_id, sample_text),
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error loading style data: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving style: {str(e)}")


def generate_preview(style_id: int, sample_text: str):
    """
    Generate a preview SVG for a specific style
    """
    try:
        # Create a temporary file for the SVG output
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as temp_file:
            output_path = temp_file.name

        # Generate a preview using the style
        hand.write(
            filename=output_path,
            lines=[sample_text[:30]],  # Use first 30 chars of sample text
            styles=[style_id],
        )

        # Read the generated SVG file
        with open(output_path, "r") as f:
            svg_content = f.read()

        # Clean up the temporary file
        os.unlink(output_path)

        return svg_content
    except Exception as e:
        return f"Error generating preview: {str(e)}"
