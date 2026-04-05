#!/usr/bin/env python3
"""
generate_icons.py — Génère les icônes PWA HEIST.EXE en SVG.
Lance depuis frontend/public/icons/

Usage: python3 generate_icons.py
"""
import os

SVG_192 = '''<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 192 192">
  <rect width="192" height="192" fill="#0a0a0a"/>
  <rect x="16" y="16" width="160" height="160" fill="none" stroke="#00d4aa" stroke-width="2"/>
  <rect x="24" y="24" width="144" height="144" fill="none" stroke="#00d4aa" stroke-width="0.5" stroke-dasharray="4,4"/>
  <!-- H -->
  <rect x="36" y="60" width="12" height="72" fill="#00d4aa"/>
  <rect x="36" y="90" width="38" height="12" fill="#00d4aa"/>
  <rect x="66" y="60" width="12" height="72" fill="#00d4aa"/>
  <!-- X -->
  <line x1="88" y1="60" x2="130" y2="132" stroke="#00d4aa" stroke-width="12" stroke-linecap="round"/>
  <line x1="130" y1="60" x2="88" y2="132" stroke="#00d4aa" stroke-width="12" stroke-linecap="round"/>
  <!-- dot -->
  <rect x="140" y="148" width="12" height="12" fill="#00d4aa"/>
  <!-- scanline deco -->
  <line x1="16" y1="170" x2="176" y2="170" stroke="#00d4aa" stroke-width="0.5" opacity="0.3"/>
  <text x="20" y="185" font-family="monospace" font-size="8" fill="#00d4aa" opacity="0.5">v0.1.0</text>
</svg>'''

SVG_512 = SVG_192.replace('width="192" height="192" viewBox="0 0 192 192"',
                           'width="512" height="512" viewBox="0 0 192 192"')

out_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(out_dir, exist_ok=True)

with open(os.path.join(out_dir, 'icon-192.svg'), 'w') as f:
    f.write(SVG_192)
print('  ✓ icon-192.svg')

with open(os.path.join(out_dir, 'icon-512.svg'), 'w') as f:
    f.write(SVG_512)
print('  ✓ icon-512.svg')

# Alias favicon
with open(os.path.join(out_dir, '..', 'favicon.svg'), 'w') as f:
    f.write(SVG_192)
print('  ✓ favicon.svg')

print()
print('  Note: Pour des .png réels, convertis avec:')
print('    npx @squoosh/cli --oxipng {} icon-192.svg')
print('  Ou: convert icon-192.svg -resize 192x192 icon-192.png  (ImageMagick)')
