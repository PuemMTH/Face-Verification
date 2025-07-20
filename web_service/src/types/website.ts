export interface DetectionResult {
  success: boolean;
  confidence: number | null;
  view_bbox_path: string | null;
  view_bbox_txt_path: string | null;
}

export interface SegmentationResult {
  success: boolean;
  confidence: number | null;
  view_mask_path: string | null;
}

export interface ApiStatus {
  success: boolean;
  message: string;
}

export interface PredictionResult {
  status: ApiStatus;
  detection: DetectionResult;
  segmentation: SegmentationResult;
  view_original_path: string | null;
}

export interface ApiResponse {
  width: number;
  height: number;
  original_filename: string;
  filename: string;
  prediction: PredictionResult;
}