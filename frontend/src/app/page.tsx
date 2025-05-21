"use client";
import { useState } from "react";
import {
  useGenerateHandwriting,
  useHandwritingStyles,
  useHandwritingStyle,
} from "@/lib/api-hooks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

export default function Home() {
  const [text, setText] = useState("Hello, world!");
  const [selectedStyle, setSelectedStyle] = useState<number | null>(null);
  const [generatedSvg, setGeneratedSvg] = useState<string | null>(null);

  // Fetch available handwriting styles
  const { data: stylesData, isLoading: stylesLoading } = useHandwritingStyles();

  // Fetch details for the selected style
  const { data: styleDetail } = useHandwritingStyle(selectedStyle ?? -1);

  // Mutation for generating handwriting
  const { mutate: generateHandwriting, isPending } = useGenerateHandwriting();

  const handleGenerate = () => {
    if (!text) return;

    generateHandwriting(
      {
        lines: text.split("\n"),
        styles:
          selectedStyle !== null
            ? text.split("\n").map(() => selectedStyle)
            : undefined,
        biases: text.split("\n").map(() => 0.9),
      },
      {
        onSuccess: (data) => {
          setGeneratedSvg(data.svg_content);
        },
        onError: (error) => {
          console.error("Error generating handwriting:", error);
        },
      }
    );
  };

  return (
    <div className="max-w-screen-xl mx-auto flex flex-col items-center justify-start py-12 px-4 min-h-screen">
      <h1 className="text-[64px] md:text-[129px] font-serif mb-8">Kalam3</h1>

      <div className="w-full max-w-3xl space-y-6">
        <div className="space-y-2">
          <Label htmlFor="text-input">
            Enter text to convert to handwriting
          </Label>
          <Textarea
            id="text-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type your text here..."
            className="h-24"
          />
        </div>

        <div className="space-y-2">
          <Label>Select handwriting style</Label>
          <Select
            disabled={stylesLoading}
            value={selectedStyle?.toString() || ""}
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

        {styleDetail && (
          <div className="p-4 border rounded-md bg-gray-50">
            <h3 className="font-medium mb-2">Style Preview</h3>
            <div dangerouslySetInnerHTML={{ __html: styleDetail.preview }} />
          </div>
        )}

        <Button
          onClick={handleGenerate}
          disabled={isPending}
          className="w-full"
        >
          {isPending ? "Generating..." : "Generate Handwriting"}
        </Button>

        {generatedSvg && (
          <div className="mt-8 p-4 border rounded-md">
            <h3 className="font-medium mb-2">Generated Handwriting</h3>
            <div dangerouslySetInnerHTML={{ __html: generatedSvg }} />
          </div>
        )}
      </div>
    </div>
  );
}
