import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./axios";

// Types for handwriting API
export interface GenerateHandwritingParams {
  lines: string[];
  biases?: number[];
  styles?: number[];
  stroke_colors?: string[];
  stroke_widths?: number[];
}

export interface GenerateHandwritingResponse {
  status: string;
  svg_content: string;
  message: string;
}

export interface StylesListResponse {
  status: string;
  styles: number[];
  count: number;
}

export interface StyleDetailResponse {
  status: string;
  style_id: number;
  stroke_count: number;
  sample_text: string;
  preview: string;
}

export interface GenerateA4PageParams {
  text: string;
  style_id?: number;
  bias?: number;
  stroke_color?: string;
  stroke_width?: number;
}

export interface GenerateA4PageResponse {
  status: string;
  svg_content: string;
  message: string;
  line_count: number;
  page_format: string;
}

// Hook to generate handwriting
export const useGenerateHandwriting = () => {
  return useMutation({
    mutationFn: async (params: GenerateHandwritingParams) => {
      const response = await api.post<GenerateHandwritingResponse>(
        "/handwriting/generate",
        params
      );
      return response.data;
    },
  });
};

// Hook to get all available styles
export const useHandwritingStyles = () => {
  return useQuery({
    queryKey: ["handwritingStyles"],
    queryFn: async () => {
      const response = await api.get<StylesListResponse>("/handwriting/styles");
      return response.data;
    },
  });
};

// Hook to get details for a specific style
export const useHandwritingStyle = (styleId: number) => {
  return useQuery({
    queryKey: ["handwritingStyle", styleId],
    queryFn: async () => {
      const response = await api.get<StyleDetailResponse>(
        `/handwriting/styles/${styleId}`
      );
      return response.data;
    },
    enabled: styleId !== undefined && styleId >= 0,
  });
};

// Hook to generate handwriting on an A4 page
export const useGenerateA4Page = () => {
  return useMutation({
    mutationFn: async (params: GenerateA4PageParams) => {
      const response = await api.post<GenerateA4PageResponse>(
        "/handwriting/a4page",
        params
      );
      return response.data;
    },
  });
};
