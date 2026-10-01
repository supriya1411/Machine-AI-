export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error_code?: string | null;
  meta?: Record<string, any>;
}

export function createSuccessResponse<T>(data: T, message?: string, meta?: Record<string, any>): ApiResponse<T> {
  return {
    success: true,
    data,
    message,
    error_code: null,
    meta,
  };
}

export function createErrorResponse(message: string, errorCode: string = 'BAD_REQUEST', meta?: Record<string, any>): ApiResponse<null> {
  return {
    success: false,
    data: null,
    message,
    error_code: errorCode,
    meta,
  };
}
