import os
import numpy as np
import tensorflow as tf
import svgwrite
from app.utils import drawing


class Hand:
    """Hand implementation that uses the exported frozen model."""

    def __init__(self, model_path="saved_model/saved_model.pb"):
        """Initialize the hand with the exported frozen model."""
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Only show errors, not warnings/info
        self.model_path = model_path
        self.session = None

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
        filename,
        lines,
        biases=None,
        styles=None,
        stroke_colors=None,
        stroke_widths=None,
    ):
        """Generate handwriting for the given text and save as SVG."""
        # Match original Hand validation
        valid_char_set = set(drawing.alphabet)
        for line_num, line in enumerate(lines):
            if len(line) > 75:
                raise ValueError(
                    (
                        "Each line must be at most 75 characters. "
                        "Line {} contains {}"
                    ).format(line_num, len(line))
                )

            for char in line:
                if char not in valid_char_set:
                    raise ValueError(
                        (
                            "Invalid character {} detected in line {}. "
                            "Valid character set is {}"
                        ).format(char, line_num, valid_char_set)
                    )

        strokes = self._sample(lines, biases=biases, styles=styles)
        self._draw(
            strokes,
            lines,
            filename,
            stroke_colors=stroke_colors,
            stroke_widths=stroke_widths,
        )

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

    def _draw(self, strokes, lines, filename, stroke_colors=None, stroke_widths=None):
        """Draw the strokes as an SVG file."""
        stroke_colors = stroke_colors or ["black"] * len(lines)
        stroke_widths = stroke_widths or [2] * len(lines)

        line_height = 60
        view_width = 1000
        view_height = line_height * (len(strokes) + 1)

        dwg = svgwrite.Drawing(filename=filename)
        dwg.viewbox(width=view_width, height=view_height)
        dwg.add(dwg.rect(insert=(0, 0), size=(view_width, view_height), fill="white"))

        initial_coord = np.array([0, -(3 * line_height / 4)])
        for offsets, line, color, width in zip(
            strokes, lines, stroke_colors, stroke_widths
        ):

            if not line:
                initial_coord[1] -= line_height
                continue

            offsets[:, :2] *= 1.5
            strokes = drawing.offsets_to_coords(offsets)
            strokes = drawing.denoise(strokes)
            strokes[:, :2] = drawing.align(strokes[:, :2])

            strokes[:, 1] *= -1
            strokes[:, :2] -= strokes[:, :2].min() + initial_coord
            strokes[:, 0] += (view_width - strokes[:, 0].max()) / 2

            prev_eos = 1.0
            p = "M{},{} ".format(0, 0)
            for x, y, eos in zip(*strokes.T):
                p += "{}{},{} ".format("M" if prev_eos == 1.0 else "L", x, y)
                prev_eos = eos
            path = svgwrite.path.Path(p)
            path = path.stroke(color=color, width=width, linecap="round").fill("none")
            dwg.add(path)

            initial_coord[1] -= line_height

        dwg.save()
        print(f"SVG saved to {filename}")
