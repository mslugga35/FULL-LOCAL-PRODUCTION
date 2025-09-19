/**
 * AI-Enhanced OCR Text Processor
 * Uses Claude or GPT-4 Vision to extract and clean text from images
 */

const axios = require('axios');
const fs = require('fs').promises;

class AITextEnhancer {
  constructor(config = {}) {
    // Can use Claude, OpenAI, or both
    this.claudeApiKey = config.claudeApiKey || process.env.CLAUDE_API_KEY;
    this.openaiApiKey = config.openaiApiKey || process.env.OPENAI_API_KEY;
  }

  /**
   * Use Claude Vision to extract text from image
   */
  async extractWithClaude(imagePath) {
    if (!this.claudeApiKey) {
      throw new Error('Claude API key not configured');
    }

    try {
      // Read image as base64
      const imageBuffer = await fs.readFile(imagePath);
      const base64Image = imageBuffer.toString('base64');

      const response = await axios.post(
        'https://api.anthropic.com/v1/messages',
        {
          model: 'claude-3-opus-20240229',
          max_tokens: 1000,
          messages: [{
            role: 'user',
            content: [
              {
                type: 'image',
                source: {
                  type: 'base64',
                  media_type: 'image/jpeg',
                  data: base64Image
                }
              },
              {
                type: 'text',
                text: `Extract all text from this sports betting screenshot.
                      Focus on:
                      1. The capper/tipster name
                      2. All betting picks (team names, ML, spreads, totals)
                      3. Unit sizes
                      4. Any odds or lines

                      Format the output clearly with:
                      - Capper name on first line
                      - Each pick on a new line
                      - Include all betting details (ML, spread, units)

                      Clean up any OCR artifacts but preserve the actual betting information.`
              }
            ]
          }]
        },
        {
          headers: {
            'x-api-key': this.claudeApiKey,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
          }
        }
      );

      return response.data.content[0].text;
    } catch (error) {
      console.error('Claude Vision error:', error.message);
      return null;
    }
  }

  /**
   * Use GPT-4 Vision to extract text from image
   */
  async extractWithGPT(imagePath) {
    if (!this.openaiApiKey) {
      throw new Error('OpenAI API key not configured');
    }

    try {
      // Read image as base64
      const imageBuffer = await fs.readFile(imagePath);
      const base64Image = imageBuffer.toString('base64');

      const response = await axios.post(
        'https://api.openai.com/v1/chat/completions',
        {
          model: 'gpt-4-vision-preview',
          messages: [
            {
              role: 'user',
              content: [
                {
                  type: 'text',
                  text: `Extract and clean all text from this sports betting image.
                         Make the text clear and easy to read.
                         Include:
                         - Capper/tipster name
                         - All picks with teams and bet types
                         - Units and odds
                         Format cleanly with each pick on its own line.`
                },
                {
                  type: 'image_url',
                  image_url: {
                    url: `data:image/jpeg;base64,${base64Image}`
                  }
                }
              ]
            }
          ],
          max_tokens: 500
        },
        {
          headers: {
            'Authorization': `Bearer ${this.openaiApiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      return response.data.choices[0].message.content;
    } catch (error) {
      console.error('GPT-4 Vision error:', error.message);
      return null;
    }
  }

  /**
   * Extract text using available AI service
   */
  async extractText(imagePath) {
    // Try Claude first (often better for structured extraction)
    if (this.claudeApiKey) {
      const claudeResult = await this.extractWithClaude(imagePath);
      if (claudeResult) return claudeResult;
    }

    // Fallback to GPT-4 Vision
    if (this.openaiApiKey) {
      const gptResult = await this.extractWithGPT(imagePath);
      if (gptResult) return gptResult;
    }

    throw new Error('No AI service available for text extraction');
  }

  /**
   * Clean and structure the extracted text
   */
  formatExtractedText(rawText) {
    if (!rawText) return '';

    // Split into lines and clean
    const lines = rawText.split('\n').map(l => l.trim()).filter(l => l);

    let formatted = '';
    let capperName = '';

    // Find capper name (usually first non-pick line)
    for (const line of lines) {
      if (!line.match(/ML|spread|total|over|under|\d+u/i) &&
          !line.match(/^\d+/) &&
          line.length < 30) {
        capperName = line;
        break;
      }
    }

    if (capperName) {
      formatted = `${capperName}\n`;
      formatted += '━━━━━━━━━\n';
    }

    // Add picks
    const picks = lines.filter(line =>
      line.match(/ML|spread|total|over|under|\d+u|[+-]\d+/i) ||
      line.match(/\b(unit|units)\b/i)
    );

    for (const pick of picks) {
      formatted += `• ${pick}\n`;
    }

    return formatted;
  }
}

module.exports = AITextEnhancer;