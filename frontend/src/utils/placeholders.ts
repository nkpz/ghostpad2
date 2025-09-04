/**
 * Replace placeholders in message content with actual values
 */
export function replacePlaceholders(
  content: string, 
  userName: string, 
  charName: string
): string {
  return content
    .replace(/\{\{user\}\}/g, userName)
    .replace(/\{\{char\}\}/g, charName)
    .replace(/\[\[user\]\]/g, userName)
    .replace(/\[\[char\]\]/g, charName);
}