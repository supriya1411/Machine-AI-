import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiResponse } from '../dto/api-response.dto';

@Injectable()
export class TransformInterceptor<T>
  implements NestInterceptor<T, ApiResponse<T>>
{
  intercept(
    context: ExecutionContext,
    next: CallHandler,
  ): Observable<ApiResponse<T>> {
    return next.handle().pipe(
      map((res) => {
        // If already structured as an ApiResponse (has success & data properties), return directly
        if (res && typeof res === 'object' && 'success' in res && 'data' in res) {
          return res;
        }

        // Handle file buffers / CSV string downloads or raw responses
        if (typeof res === 'string' && (res.startsWith('data:text/csv') || res.includes(','))) {
          return res as any;
        }

        return {
          success: true,
          data: res !== undefined ? res : null,
          message: null,
          error_code: null,
          meta: res?.meta || undefined,
        };
      }),
    );
  }
}
