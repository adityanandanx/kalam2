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
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";

export default function A4Page() {
  const [text, setText] = useState(
    "Dear Friend,\n\nI hope this letter finds you well. I wanted to take a moment to write to you and share my thoughts. The weather has been lovely here, and I've been enjoying long walks in the park.\n\nIt's been a while since we last spoke, and I miss our conversations. Perhaps we could meet for coffee sometime next week?\n\nLooking forward to your reply.\n\nBest wishes,\nYour friend"
  );
  const [selectedStyle, setSelectedStyle] = useState<number>(0);
  const [color, setColor] = useState<string>("black");
  const [lineHeight, setLineHeight] = useState<number>(1.5);
  const [paragraphSpacing, setParagraphSpacing] = useState<number>(2.0);
  const [linesPerPage, setLinesPerPage] = useState<number>(25);
  const [generatedPages, setGeneratedPages] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState<number>(0);
  const [lineCount, setLineCount] = useState<number>(0);
  const [pageCount, setPageCount] = useState<number>(0);

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
        line_height: lineHeight,
        paragraph_spacing: paragraphSpacing,
        lines_per_page: linesPerPage,
      },
      {
        onSuccess: (data) => {
          setGeneratedPages(data.pages);
          setCurrentPage(0);
          setLineCount(data.line_count);
          setPageCount(data.page_count);
        },
        onError: (error) => {
          console.error("Error generating A4 handwriting:", error);
        },
      }
    );
  };

  const downloadCurrentPage = () => {
    if (!generatedPages.length || currentPage >= generatedPages.length) return;

    const svgContent = generatedPages[currentPage];
    const blob = new Blob([svgContent], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `handwritten-a4-page-${currentPage + 1}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadAllPages = () => {
    if (!generatedPages.length) return;

    // For now, we'll just trigger downloads for each page separately
    // In a real app, you might want to create a ZIP file
    generatedPages.forEach((svgContent, index) => {
      const blob = new Blob([svgContent], { type: "image/svg+xml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `handwritten-a4-page-${index + 1}.svg`;
      document.body.appendChild(a);

      // Use setTimeout to space out the downloads slightly
      setTimeout(() => {
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, index * 100);
    });
  };

  const goToPage = (pageNumber: number) => {
    if (pageNumber >= 0 && pageNumber < generatedPages.length) {
      setCurrentPage(pageNumber);
    }
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
            Enter text to convert to handwriting on A4 pages
          </Label>
          <Textarea
            id="text-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type your text here..."
            className="h-40"
          />
          <p className="text-sm text-gray-500">
            The text will be automatically formatted to fit A4 pages with proper
            margins. Empty lines will be treated as paragraph breaks. Long text
            will be split across multiple pages.
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

        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Line Height: {lineHeight.toFixed(1)}</Label>
              <span className="text-sm text-gray-500">
                (Spacing between lines)
              </span>
            </div>
            <Slider
              value={[lineHeight]}
              min={0.1}
              max={3.0}
              step={0.1}
              onValueChange={(values) => setLineHeight(values[0])}
              className="py-4"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Paragraph Spacing: {paragraphSpacing.toFixed(1)}</Label>
              <span className="text-sm text-gray-500">
                (Extra space between paragraphs)
              </span>
            </div>
            <Slider
              value={[paragraphSpacing]}
              min={0.1}
              max={4.0}
              step={0.1}
              onValueChange={(values) => setParagraphSpacing(values[0])}
              className="py-4"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Lines Per Page: {linesPerPage}</Label>
              <span className="text-sm text-gray-500">
                (Maximum lines on each page)
              </span>
            </div>
            <Slider
              value={[linesPerPage]}
              min={10}
              max={40}
              step={1}
              onValueChange={(values) => setLinesPerPage(values[0])}
              className="py-4"
            />
          </div>
        </div>

        <Button
          onClick={handleGenerate}
          disabled={isPending}
          className="w-full"
        >
          {isPending ? "Generating..." : "Generate A4 Handwriting"}
        </Button>

        {generatedPages.length > 0 && (
          <div className="mt-8 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-medium">Generated A4 Handwriting</h3>
              <div className="flex space-x-2 items-center">
                <span className="text-sm text-gray-500">
                  {lineCount} lines on {pageCount}{" "}
                  {pageCount === 1 ? "page" : "pages"}
                </span>
                <Button
                  onClick={downloadCurrentPage}
                  variant="outline"
                  size="sm"
                >
                  Download Page
                </Button>
                {pageCount > 1 && (
                  <Button
                    onClick={downloadAllPages}
                    variant="outline"
                    size="sm"
                  >
                    Download All
                  </Button>
                )}
              </div>
            </div>

            {pageCount > 1 && (
              <div className="flex justify-between items-center">
                <Button
                  onClick={() => goToPage(currentPage - 1)}
                  disabled={currentPage <= 0}
                  variant="outline"
                  size="sm"
                >
                  Previous Page
                </Button>
                <div className="flex items-center gap-2">
                  <span>Page</span>
                  <Input
                    type="number"
                    min={1}
                    max={pageCount}
                    value={currentPage + 1}
                    onChange={(e) => goToPage(parseInt(e.target.value) - 1)}
                    className="w-16 text-center"
                  />
                  <span>of {pageCount}</span>
                </div>
                <Button
                  onClick={() => goToPage(currentPage + 1)}
                  disabled={currentPage >= pageCount - 1}
                  variant="outline"
                  size="sm"
                >
                  Next Page
                </Button>
              </div>
            )}

            <div className="border rounded-md overflow-hidden bg-gray-50 p-4">
              <div
                dangerouslySetInnerHTML={{
                  __html: generatedPages[currentPage] || "",
                }}
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
