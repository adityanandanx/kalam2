"use client";
import { useState } from "react";
import { useGenerateA4Page, useHandwritingStyles } from "@/lib/api-hooks";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import Link from "next/link";

export default function A4Page() {
  const [text, setText] = useState(
    "Dear Friend,\n\nI hope this letter finds you well. I wanted to take a moment to write to you and share my thoughts. The weather has been lovely here, and I've been enjoying long walks in the park.\n\nIt's been a while since we last spoke, and I miss our conversations. Perhaps we could meet for coffee sometime next week?\n\nLooking forward to your reply.\n\nBest wishes,\nYour friend"
  );
  const [selectedStyle, setSelectedStyle] = useState<number>(0);
  const [color, setColor] = useState<string>("black");
  const [generatedSvg, setGeneratedSvg] = useState<string | null>(null);
  const [lineCount, setLineCount] = useState<number>(0);

  // Fetch available handwriting styles
  const { data: stylesData, isLoading: stylesLoading } = useHandwritingStyles();

  // Mutation for generating A4 page handwriting
  const { mutate: generateA4Page, isPending } = useGenerateA4Page();

  const handleGenerate = () => {
    if (!text) return;

    generateA4Page(
      {
        text,
        style_id: selectedStyle,
        bias: 0.75,
        stroke_color: color,
        stroke_width: 2.0,
      },
      {
        onSuccess: (data) => {
          setGeneratedSvg(data.svg_content);
          setLineCount(data.line_count);
        },
        onError: (error) => {
          console.error("Error generating A4 handwriting:", error);
        },
      }
    );
  };

  const downloadSvg = () => {
    if (!generatedSvg) return;

    const blob = new Blob([generatedSvg], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "handwritten-a4.svg";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-screen-xl mx-auto flex flex-col items-center justify-start py-12 px-4 min-h-screen">
      <div className="w-full flex justify-between items-center mb-8">
        <h1 className="text-3xl font-serif">A4 Handwriting Generator</h1>
        <Link href="/" className="text-blue-600 hover:underline">
          Back to Home
        </Link>
      </div>

      <div className="w-full max-w-3xl space-y-6">
        <div className="space-y-2">
          <Label htmlFor="text-input">
            Enter text to convert to handwriting on an A4 page
          </Label>
          <Textarea
            id="text-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type your text here..."
            className="h-40"
          />
          <p className="text-sm text-gray-500">
            The text will be automatically formatted to fit an A4 page with
            proper margins.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Select handwriting style</Label>
            <Select
              disabled={stylesLoading}
              value={selectedStyle.toString()}
              onValueChange={(value) => setSelectedStyle(parseInt(value))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a style" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {stylesData?.styles.map((styleId) => (
                    <SelectItem key={styleId} value={styleId.toString()}>
                      Style {styleId}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Ink Color</Label>
            <Select value={color} onValueChange={(value) => setColor(value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select color" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem value="black">Black</SelectItem>
                  <SelectItem value="blue">Blue</SelectItem>
                  <SelectItem value="#0000CC">Dark Blue</SelectItem>
                  <SelectItem value="#CC0000">Red</SelectItem>
                  <SelectItem value="#006600">Green</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
        </div>

        <Button
          onClick={handleGenerate}
          disabled={isPending}
          className="w-full"
        >
          {isPending ? "Generating..." : "Generate A4 Handwriting"}
        </Button>

        {generatedSvg && (
          <div className="mt-8 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-medium">Generated A4 Handwriting</h3>
              <div className="flex space-x-2">
                <span className="text-sm text-gray-500">
                  {lineCount} lines generated
                </span>
                <Button onClick={downloadSvg} variant="outline" size="sm">
                  Download SVG
                </Button>
              </div>
            </div>

            <div className="border rounded-md overflow-hidden bg-gray-50 p-4">
              <div
                dangerouslySetInnerHTML={{ __html: generatedSvg }}
                className="w-full"
                style={{ maxWidth: "100%", height: "auto" }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
