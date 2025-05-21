from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional, Dict, Any
import os
import tempfile
import numpy as np
from app.services.handwriting import Hand, LayoutConfig, TextSegment
from app.utils import drawing  # Import drawing module for character validation

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

        print(svg_content)

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


@router.post("/markdown")
async def generate_from_markdown(
    markdown_text: str = Body(...),
    style_options: Optional[Dict[str, Dict[str, Any]]] = Body(None),
    default_style: Optional[int] = Body(0),
):
    """
    Generate handwriting from markdown text with styles for different markdown elements

    Args:
        markdown_text: The markdown text to convert to handwriting
        style_options: Optional styling options for different markdown elements
            Example: {
                'h1': {'size': 1.5, 'color': 'red', 'width': 3},
                'h2': {'size': 1.3, 'color': 'blue', 'width': 2.5},
                'bold': {'width': 3, 'color': 'black'},
                'italic': {'style': 1},
                'code': {'color': 'gray'},
                'link': {'color': 'blue'}
            }
        default_style: The base style ID to use for the handwriting
    """
    # try:
    #     # Ensure markdown_text is not empty
    #     if not markdown_text:
    #         markdown_text = " "  # Provide a space as minimum content

    #     # Parse the markdown text
    #     lines, style_params = markdown_parser.parse(markdown_text, style_options)

    #     # Debug information
    #     print(f"Parsed markdown into {len(lines)} lines:")
    #     for i, line in enumerate(lines):
    #         print(f"Line {i}: '{line}' (length: {len(line)})")

    #     # Filter out any empty lines and sanitize text to ensure it works with the handwriting model
    #     valid_lines = []
    #     valid_params = []
    #     valid_char_set = set(drawing.alphabet)

    #     for i, line in enumerate(lines):
    #         # Skip completely empty lines
    #         if line != "":
    #             # Sanitize the line - replace any unsupported characters with spaces
    #             sanitized_line = ""
    #             for char in line:
    #                 if char in valid_char_set:
    #                     sanitized_line += char
    #                 else:
    #                     sanitized_line += " "

    #             # Only add non-empty sanitized lines
    #             if sanitized_line.strip():
    #                 valid_lines.append(sanitized_line)
    #                 valid_params.append(style_params[i])
    #                 print(f"Added sanitized line: '{sanitized_line}'")

    #     # Ensure we have at least one line
    #     if not valid_lines:
    #         valid_lines = ["Hello"]  # Use a simple word instead of just a space
    #         valid_params = [
    #             {
    #                 "stroke_color": "#000000",
    #                 "stroke_width": 2,
    #                 "style": default_style,
    #                 "bias": 0.5,
    #             }
    #         ]
    #         print("No valid lines found, using default 'Hello' text")

    #     # Prepare parameters for the handwriting service
    #     stroke_colors = [param.get("stroke_color", "black") for param in valid_params]
    #     stroke_widths = [param.get("stroke_width", 2) for param in valid_params]
    #     size_scales = [param.get("size_scaling", 1.0) for param in valid_params]
    #     styles = [param.get("style", default_style) for param in valid_params]
    #     biases = [param.get("bias", 0.5) for param in valid_params]

    #     # Create a temporary file for the SVG output
    #     with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as temp_file:
    #         output_path = temp_file.name

    #     # Generate the handwriting
    #     hand.write(
    #         filename=output_path,
    #         lines=valid_lines,
    #         biases=biases,
    #         styles=styles,
    #         stroke_colors=stroke_colors,
    #         stroke_widths=stroke_widths,
    #         size_scales=size_scales,
    #     )

    #     # Read the generated SVG file
    #     with open(output_path, "r") as f:
    #         svg_content = f.read()

    #     # Clean up the temporary file
    #     os.unlink(output_path)

    #     return {
    #         "status": "success",
    #         "svg_content": svg_content,
    #         "message": "Markdown handwriting generated successfully",
    #         "lines_count": len(valid_lines),
    #         "lines": valid_lines,  # Include the processed lines for debugging
    #         "original_lines": lines,  # Include original parsed lines for debugging
    #     }
    # except Exception as e:
    #     import traceback

    #     error_details = traceback.format_exc()
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"Error generating markdown handwriting: {str(e)}\n{error_details}",
    #     )
    pass


@router.post("/advanced")
async def generate_advanced_handwriting(
    text: str = Body(...),
    segmentation_level: str = Body("line"),
    default_style: int = Body(0),
    default_bias: float = Body(0.5),
    default_stroke_color: str = Body("black"),
    default_stroke_width: float = Body(2.0),
    default_scale: float = Body(1.0),
    segment_styles: Optional[List[Dict[str, Any]]] = Body(None),
    layout: Optional[Dict[str, Any]] = Body(None),
):
    """
    Generate handwriting with advanced styling and layout options.

    Args:
        text: The text to convert to handwriting
        segmentation_level: How to segment the text - 'line', 'word', or 'character'
        default_style: The default handwriting style ID
        default_bias: The default bias value (randomness)
        default_stroke_color: The default stroke color
        default_stroke_width: The default stroke width
        default_scale: The default size scaling factor
        segment_styles: Optional list of style overrides for specific segments
            Format: [{"index": [line_idx, segment_idx], "style_id": 1, "color": "red", ...}]
        layout: Optional layout configuration
            Format: {"line_spacing": 1.2, "word_spacing": 1.0, "alignment": "left", ...}
    """
    try:
        # Process the text into segments
        segments_by_line = hand.process_text(
            text=text,
            segmentation=segmentation_level,
            default_style=default_style,
            default_bias=default_bias,
            default_color=default_stroke_color,
            default_width=default_stroke_width,
            default_scale=default_scale,
        )

        # Apply any custom segment styles if provided
        if segment_styles:
            for style_override in segment_styles:
                if "index" in style_override:
                    line_idx, segment_idx = style_override["index"]

                    # Skip if index is out of range
                    if 0 <= line_idx < len(segments_by_line) and 0 <= segment_idx < len(
                        segments_by_line[line_idx]
                    ):

                        segment = segments_by_line[line_idx][segment_idx]

                        # Apply style overrides
                        if "style_id" in style_override:
                            segment.style_id = style_override["style_id"]
                        if "bias" in style_override:
                            segment.bias = style_override["bias"]
                        if "color" in style_override:
                            segment.stroke_color = style_override["color"]
                        if "width" in style_override:
                            segment.stroke_width = style_override["width"]
                        if "scale" in style_override:
                            segment.scale = style_override["scale"]

        # Create layout configuration
        layout_config = None
        if layout:
            layout_config = LayoutConfig(
                line_spacing=layout.get("line_spacing", 1.2),
                word_spacing=layout.get("word_spacing", 1.0),
                char_spacing=layout.get("char_spacing", 1.0),
                alignment=layout.get("alignment", "left"),
                max_width=layout.get("max_width", None),
            )

        # Create a temporary file for the SVG output
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as temp_file:
            output_path = temp_file.name

        # Generate the handwriting with segments
        hand.write_segments(
            filename=output_path,
            segments_by_line=segments_by_line,
            layout_config=layout_config,
        )

        # Read the generated SVG file
        with open(output_path, "r") as f:
            svg_content = f.read()

        # Clean up the temporary file
        os.unlink(output_path)

        # Count segments for reporting
        segment_count = sum(len(line) for line in segments_by_line)

        return {
            "status": "success",
            "svg_content": svg_content,
            "message": "Advanced handwriting generated successfully",
            "segmentation_level": segmentation_level,
            "segment_count": segment_count,
            "line_count": len(segments_by_line),
        }

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating advanced handwriting: {str(e)}\n{error_details}",
        )


@router.post("/a4page")
async def generate_a4_page(
    text: str = Body(...),
    style_id: Optional[int] = Body(0),
    bias: Optional[float] = Body(0.5),
    stroke_color: Optional[str] = Body("black"),
    stroke_width: Optional[float] = Body(2.0),
):
    """
    Generate handwriting on an A4-sized page, automatically splitting text into lines.

    Args:
        text: The text to convert to handwriting
        style_id: The handwriting style ID to use
        bias: The bias value (randomness factor)
        stroke_color: The color of the handwriting strokes
        stroke_width: The width of the handwriting strokes
    """
    try:
        # A4 dimensions in pixels (assuming 96 DPI)
        # A4 is 210mm x 297mm, which is approximately 794 x 1123 pixels at 96 DPI
        page_width = 794
        page_height = 1123

        # Set margins (in pixels)
        left_margin = 75
        right_margin = 75
        top_margin = 100
        bottom_margin = 100

        # Calculate usable width for text
        usable_width = page_width - left_margin - right_margin

        # Estimate characters per line based on average character width
        # Assuming average character width is about 10px * scale factor
        char_width = 10
        chars_per_line = max(1, int(usable_width / char_width))

        # Process and respect newline characters
        paragraphs = text.split("\n")
        lines = []

        # Process each paragraph separately to respect newlines
        for paragraph in paragraphs:
            if not paragraph.strip():
                # Keep empty paragraphs as empty lines
                lines.append("")
                continue

            words = paragraph.split()
            current_line = ""

            for word in words:
                # Check if adding this word would exceed the line width
                if len(current_line) + len(word) + 1 <= chars_per_line:
                    current_line += " " + word if current_line else word
                else:
                    # Line is full, add it to lines and start a new line
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            # Add the last line if it's not empty
            if current_line:
                lines.append(current_line)

        # Create layout configuration for A4 page
        layout_config = LayoutConfig(
            line_spacing=1.5,
            word_spacing=1.0,
            char_spacing=1.0,
            alignment="left",
            max_width=usable_width,
        )

        # Create segments from lines
        segments_by_line = []
        for line in lines:
            segment = TextSegment(
                text=line,
                style_id=style_id,
                bias=bias,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                scale=1.0,
            )
            segments_by_line.append([segment])

        # Create a temporary file for the SVG output
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as temp_file:
            output_path = temp_file.name

        # Generate the handwriting with A4 dimensions
        hand.write_segments(
            filename=output_path,
            segments_by_line=segments_by_line,
            layout_config=layout_config,
            page_dimensions=(page_width, page_height),
            margins=(left_margin, top_margin, right_margin, bottom_margin),
        )

        # Read the generated SVG file
        with open(output_path, "r") as f:
            svg_content = f.read()

        # Clean up the temporary file
        os.unlink(output_path)

        return {
            "status": "success",
            "svg_content": svg_content,
            "message": "A4 page handwriting generated successfully",
            "line_count": len(lines),
            "page_format": "A4",
        }
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating A4 page handwriting: {str(e)}\n{error_details}",
        )
