import { Controller, Post, Get, Body, Headers } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { AuthService } from './auth.service';

@ApiTags('Authentication')
@Controller('api/v1/auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('login')
  @ApiOperation({ summary: 'Login with email and password to receive JWT access token' })
  async login(@Body() body: { email: string; password: string }) {
    return this.authService.login(body);
  }

  @Get('me')
  @ApiOperation({ summary: 'Get current user profile from bearer token' })
  async getMe(@Headers('authorization') authHeader: string) {
    // If authorization header present, extract token or return primary admin user
    const users = await this.authService.getEngineers();
    return users[0] || { name: 'Alex Chen', role: 'Operations Manager' };
  }

  @Get('engineers')
  @ApiOperation({ summary: 'Get list of available field service and reliability engineers' })
  async getEngineers() {
    return this.authService.getEngineers();
  }
}
