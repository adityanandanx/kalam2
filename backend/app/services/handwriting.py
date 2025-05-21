import os
import numpy as np
import tensorflow as tf
import svgwrite
from app.utils import drawing
from typing import List, Dict, Any, Optional, Union, Tuple


class TextSegment:
    """
    A segment of text with its own styling properties.
    Can represent a character, word, or other text unit.
    """

    def __init__(
        self,
        text: str,
        style_id: int = 0,
        bias: float = 0.5,
        stroke_color: str = "black",
        stroke_width: float = 2.0,
        scale: float = 1.0,
    ):
        """Initialize a text segment with styling properties."""
        self.text = text
        self.style_id = style_id
        self.bias = bias
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.scale = scale
        self.strokes = None  # Will be populated after sampling


class LayoutConfig:
    """Configuration for text layout."""

    def __init__(
        self,
        line_spacing: float = 1.2,
        word_spacing: float = 1.0,
        char_spacing: float = 1.0,
        alignment: str = "left",
        max_width: Optional[float] = None,
    ):
        """Initialize layout configuration."""
        self.line_spacing = line_spacing  # As a multiple of the base line height
        self.word_spacing = word_spacing  # As a multiple of the default space width
        self.char_spacing = (
            char_spacing  # As a multiple of the default character spacing
        )
        self.alignment = alignment  # 'left', 'center', 'right', or 'justify'
        self.max_width = max_width  # Maximum width for text wrapping, None for no limit


class Hand:
    """Hand implementation that uses the exported frozen model."""

    def __init__(self, model_path="saved_model/saved_model.pb"):
        """Initialize the hand with the exported frozen model."""
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Only show errors, not warnings/info
        self.model_path = model_path
        self.session = None
        self.base_line_height = 60  # Base line height in pixels

        # Load the model
        self._load_model()

    def _load_model(self):
        """Load the frozen model."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        # TensorFlow 2.x way to load saved model
        self.model = tf.saved_model.load(os.path.dirname(self.model_path))
        print("Model loaded in native TensorFlow 2.x format!")

    def write(
        self,
        filename: str,
        lines: List[str],
        biases: Optional[List[float]] = None,
        styles: Optional[List[int]] = None,
        stroke_colors: Optional[List[str]] = None,
        stroke_widths: Optional[List[float]] = None,
        scales: Optional[List[float]] = None,
    ):
        """
        Generate handwriting for the given text lines and save as SVG.
        This method retains backward compatibility with the original API.
        """
        # Create text segments from lines (for backward compatibility)
        segments_by_line = []
        for i, line in enumerate(lines):
            style = styles[i] if styles and i < len(styles) else 0
            bias = biases[i] if biases and i < len(biases) else 0.5
            color = (
                stroke_colors[i]
                if stroke_colors and i < len(stroke_colors)
                else "black"
            )
            width = (
                stroke_widths[i] if stroke_widths and i < len(stroke_widths) else 2.0
            )
            scale_factor = scales[i] if scales and i < len(scales) else 1.0

            segment = TextSegment(
                text=line,
                style_id=style,
                bias=bias,
                stroke_color=color,
                stroke_width=width,
                scale=scale_factor,
            )
            segments_by_line.append([segment])

        # Use the new method with the segments
        self.write_segments(filename, segments_by_line)

    def write_segments(
        self,
        filename: str,
        segments_by_line: List[List[TextSegment]],
        layout_config: Optional[LayoutConfig] = None,
        page_dimensions: Optional[Tuple[float, float]] = None,
        margins: Optional[Tuple[float, float, float, float]] = None,
    ):
        """
        Generate handwriting for the given text segments and save as SVG.
        Args:
            filename: Path to save the SVG file
            segments_by_line: List of lists of TextSegment objects, grouped by line
            layout_config: Optional layout configuration
            page_dimensions: Optional (width, height) for the page in pixels
            margins: Optional (left, top, right, bottom) margins in pixels
        """
        # Use default layout config if none provided
        if layout_config is None:
            layout_config = LayoutConfig()

        # Validate all characters in segments
        self._validate_segments(segments_by_line)

        # Sample strokes for each segment
        self._sample_segments(segments_by_line)

        # Draw all segments with their respective styling
        self._draw_segments(
            filename, segments_by_line, layout_config, page_dimensions, margins
        )

    def process_text(
        self,
        text: str,
        segmentation: str = "line",
        default_style: int = 0,
        default_bias: float = 0.5,
        default_color: str = "black",
        default_width: float = 2.0,
        default_scale: float = 1.0,
    ) -> List[List[TextSegment]]:
        """
        Process input text into segments based on the specified segmentation type.
        Args:
            text: The input text to process
            segmentation: Segmentation type - 'line', 'word', or 'character'
            default_*: Default styling properties for all segments

        Returns:
            List of lists of TextSegment objects, grouped by line
        """
        # Split text into lines first
        lines = text.split("\n")
        segments_by_line = []

        for line in lines:
            line_segments = []

            if segmentation == "line":
                # One segment per line
                if line:
                    line_segments.append(
                        TextSegment(
                            text=line,
                            style_id=default_style,
                            bias=default_bias,
                            stroke_color=default_color,
                            stroke_width=default_width,
                            scale=default_scale,
                        )
                    )

            elif segmentation == "word":
                # Segment by words (split by spaces)
                words = line.split()
                for word in words:
                    line_segments.append(
                        TextSegment(
                            text=word,
                            style_id=default_style,
                            bias=default_bias,
                            stroke_color=default_color,
                            stroke_width=default_width,
                            scale=default_scale,
                        )
                    )

            elif segmentation == "character":
                # Segment by individual characters
                for char in line:
                    if char in drawing.alphabet:
                        line_segments.append(
                            TextSegment(
                                text=char,
                                style_id=default_style,
                                bias=default_bias,
                                stroke_color=default_color,
                                stroke_width=default_width,
                                scale=default_scale,
                            )
                        )

            segments_by_line.append(line_segments)

        return segments_by_line

    def _validate_segments(self, segments_by_line: List[List[TextSegment]]):
        """Validate all characters in the segments."""
        valid_char_set = set(drawing.alphabet)

        for line_num, line_segments in enumerate(segments_by_line):
            for segment_num, segment in enumerate(line_segments):
                if len(segment.text) > 75:
                    raise ValueError(
                        f"Each segment must be at most 75 characters. "
                        f"Line {line_num}, segment {segment_num} contains {len(segment.text)}"
                    )

                for char in segment.text:
                    if char not in valid_char_set:
                        raise ValueError(
                            f"Invalid character '{char}' detected in line {line_num}, "
                            f"segment {segment_num}. Valid character set is {valid_char_set}"
                        )

    def _sample_segments(self, segments_by_line: List[List[TextSegment]]):
        """Sample strokes for each segment and store in the segment objects."""
        # Flatten all segments for batch processing
        all_segments = []
        for line_segments in segments_by_line:
            all_segments.extend(line_segments)

        # Skip if no segments
        if not all_segments:
            return

        # Prepare data for model input
        texts = [segment.text for segment in all_segments]
        biases = [segment.bias for segment in all_segments]
        styles = [segment.style_id for segment in all_segments]

        # Generate strokes for all segments
        strokes = self._sample(texts, biases=biases, styles=styles)

        # Assign strokes back to segments
        for i, segment in enumerate(all_segments):
            segment.strokes = strokes[i]

    def _sample(self, lines, biases=None, styles=None):
        """Sample from the model to generate handwriting strokes."""
        num_samples = len(lines)
        max_tsteps = 40 * max([len(i) for i in lines])

        # Convert string biases to float if necessary
        if biases is not None:
            biases = [float(b) if isinstance(b, str) else b for b in biases]
        else:
            biases = [0.5] * num_samples

        x_prime = np.zeros([num_samples, 1200, 3])
        x_prime_len = np.zeros([num_samples])
        chars = np.zeros([num_samples, 120])
        chars_len = np.zeros([num_samples])

        if styles is not None:
            for i, (cs, style) in enumerate(zip(lines, styles)):
                try:
                    # Use the original approach - load style from files
                    x_p = np.load(f"styles/style-{style}-strokes.npy")
                    c_p = (
                        np.load(f"styles/style-{style}-chars.npy")
                        .tobytes()
                        .decode("utf-8")
                    )

                    c_p = str(c_p) + " " + cs
                    c_p = drawing.encode_ascii(c_p)
                    c_p = np.array(c_p)

                    x_prime[i, : len(x_p), :] = x_p
                    x_prime_len[i] = len(x_p)
                    chars[i, : len(c_p)] = c_p
                    chars_len[i] = len(c_p)
                except (FileNotFoundError, IOError) as e:
                    print(
                        f"Warning: Style file not found for style {style}. Using fallback approach."
                    )
                    # Fallback to the one-hot encoding approach
                    one_hot = np.zeros([1200, 3])
                    one_hot[0 : len(drawing.alphabet)] = np.eye(3)[1]
                    x_prime[i] = one_hot
                    x_prime_len[i] = len(drawing.alphabet)

                    encoded = drawing.encode_ascii(cs)
                    chars[i, : len(encoded)] = encoded
                    chars_len[i] = len(encoded)
        else:
            for i, cs in enumerate(lines):
                encoded = drawing.encode_ascii(cs)
                chars[i, : len(encoded)] = encoded
                chars_len[i] = len(encoded)

        # Convert numpy arrays to TensorFlow tensors
        x_prime_tensor = tf.convert_to_tensor(x_prime, dtype=tf.float32)
        x_prime_len_tensor = tf.convert_to_tensor(
            x_prime_len, dtype=tf.int32
        )  # Changed to int32
        prime_tensor = tf.convert_to_tensor(styles is not None, dtype=tf.bool)
        num_samples_tensor = tf.convert_to_tensor(num_samples, dtype=tf.int32)
        sample_tsteps_tensor = tf.convert_to_tensor(max_tsteps, dtype=tf.int32)
        chars_tensor = tf.convert_to_tensor(chars, dtype=tf.int32)  # Changed to int32
        chars_len_tensor = tf.convert_to_tensor(
            chars_len, dtype=tf.int32
        )  # Changed to int32
        biases_tensor = tf.convert_to_tensor(biases, dtype=tf.float32)

        # Run the model using the signature from the saved model
        # Get the serving signature
        serving_signature = self.model.signatures["serving_default"]

        # Call the model with the appropriate inputs
        output = serving_signature(
            bias=biases_tensor,
            c=chars_tensor,
            c_len=chars_len_tensor,
            num_samples=num_samples_tensor,
            prime=prime_tensor,
            sample_tsteps=sample_tsteps_tensor,
            x_prime=x_prime_tensor,
            x_prime_len=x_prime_len_tensor,
        )

        # Extract the sampled sequence from the output dictionary
        samples = output["sampled_sequence"]

        # Convert to numpy if it's a TensorFlow tensor
        if isinstance(samples, tf.Tensor):
            samples = samples.numpy()

        # Process samples
        samples = [sample[~np.all(sample == 0.0, axis=1)] for sample in samples]
        return samples

    def _draw_segments(
        self,
        filename: str,
        segments_by_line: List[List[TextSegment]],
        layout_config: LayoutConfig,
        page_dimensions: Optional[Tuple[float, float]] = None,
        margins: Optional[Tuple[float, float, float, float]] = None,
    ):
        """Draw all segments with their respective styling."""
        # Calculate total height based on number of lines and line spacing
        line_height = self.base_line_height * layout_config.line_spacing
        num_lines = len(segments_by_line)

        # Calculate height for empty document (minimum 1 line height)
        view_height = max(1, num_lines) * line_height
        view_width = 1000  # Default width

        # Update page dimensions if provided
        if page_dimensions:
            view_width, view_height = page_dimensions

        # Default margins
        left_margin, top_margin, right_margin, bottom_margin = 0, 0, 0, 0

        # Apply margins if provided
        if margins:
            left_margin, top_margin, right_margin, bottom_margin = margins

        # Calculate usable width considering margins
        usable_width = view_width - left_margin - right_margin

        # Initialize SVG drawing
        dwg = svgwrite.Drawing(filename=filename)
        dwg.viewbox(width=view_width, height=view_height)
        dwg.add(dwg.rect(insert=(0, 0), size=(view_width, view_height), fill="white"))

        # Track current y-position with top margin
        y_position = top_margin + (
            line_height * 0.75
        )  # Start position, adjusted for baseline

        # Process each line
        for line_segments in segments_by_line:
            if not line_segments:
                # Empty line, just advance y-position
                y_position += line_height
                continue

            # Calculate line metrics and segment positions
            segment_metrics = self._calculate_segment_metrics(
                line_segments, usable_width, layout_config
            )

            # Draw each segment in the line, applying left margin to all x positions
            for segment, metrics in zip(line_segments, segment_metrics):
                if segment.strokes is None or len(segment.text) == 0:
                    continue  # Skip empty segments or those without strokes

                # Process strokes for this segment
                x_pos = metrics["x_position"] + left_margin  # Apply left margin
                width = metrics["width"]
                self._draw_segment(
                    dwg, segment, x_position=x_pos, y_position=y_position
                )

            # Advance to next line
            y_position += line_height

        # Save the SVG file
        dwg.save()
        print(f"SVG saved to {filename}")

    def _calculate_segment_metrics(
        self,
        line_segments: List[TextSegment],
        total_width: float,
        layout_config: LayoutConfig,
    ) -> List[Dict[str, float]]:
        """
        Calculate positioning metrics for each segment in a line.
        Returns a list of dictionaries with position and size information.
        """
        # Rough estimation of segment widths based on text length and scale
        segment_metrics = []

        # Estimate natural width for each segment
        total_natural_width = 0
        space_width = 10 * layout_config.word_spacing  # Estimated space width

        for i, segment in enumerate(line_segments):
            # Basic width estimation: ~10px per character × scale factor
            est_width = len(segment.text) * 10 * segment.scale

            # Store metrics
            metrics = {
                "natural_width": est_width,
                "x_position": 0,  # Will be set later
                "width": est_width,
            }
            segment_metrics.append(metrics)

            total_natural_width += est_width

            # Add space after segment (except for last segment)
            if i < len(line_segments) - 1:
                total_natural_width += space_width

        # Calculate actual positions based on alignment
        x_position = 0

        if layout_config.alignment == "center":
            # Center alignment: start from the middle
            x_position = (total_width - total_natural_width) / 2

        elif layout_config.alignment == "right":
            # Right alignment: start from the right
            x_position = total_width - total_natural_width

        # Otherwise left alignment (start from x=0)

        # Update x_positions for each segment
        for i, metrics in enumerate(segment_metrics):
            metrics["x_position"] = x_position
            x_position += metrics["natural_width"]

            # Add space after segment (except for last segment)
            if i < len(segment_metrics) - 1:
                x_position += space_width

        return segment_metrics

    def _draw_segment(
        self,
        dwg: svgwrite.Drawing,
        segment: TextSegment,
        x_position: float,
        y_position: float,
    ):
        """Draw a single text segment at the specified position."""
        # Set up initial transforms
        offsets = segment.strokes
        strokes = drawing.offsets_to_coords(offsets)
        strokes = drawing.denoise(strokes)

        # Apply scaling
        offsets[:, :2] *= 1.5 * segment.scale

        # Convert back to coordinates and align
        strokes = drawing.offsets_to_coords(offsets)
        strokes[:, :2] = drawing.align(strokes[:, :2])

        # Flip y-coordinates and position the segment
        strokes[:, 1] *= -1

        # Calculate positioning adjustment
        x_min, y_min = strokes[:, :2].min(axis=0)

        # Adjust for baseline and position
        position_adjustment = np.array([x_position - x_min, y_position - y_min])
        strokes[:, :2] += position_adjustment

        # Create SVG path
        prev_eos = 1.0
        p = "M{},{} ".format(strokes[0, 0], strokes[0, 1])

        for x, y, eos in zip(*strokes.T):
            p += "{}{},{} ".format("M" if prev_eos == 1.0 else "L", x, y)
            prev_eos = eos

        # Add the path to the drawing
        path = svgwrite.path.Path(p)
        path = path.stroke(
            color=segment.stroke_color, width=segment.stroke_width, linecap="round"
        ).fill("none")

        dwg.add(path)
