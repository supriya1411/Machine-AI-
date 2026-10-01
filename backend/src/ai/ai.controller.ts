import { Controller, Post, Body } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { AiService } from './ai.service';

@ApiTags('AI Assistant')
@Controller('api/v1/ai')
export class AiController {
  constructor(private readonly aiService: AiService) {}

  @Post('query')
  @ApiOperation({ summary: 'Submit natural language query grounded in database evidence' })
  async query(@Body() body: { query: string }) {
    return this.aiService.processQuery(body?.query);
  }
}
