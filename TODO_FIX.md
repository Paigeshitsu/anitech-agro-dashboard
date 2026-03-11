# TODO - Fix Home Page Misalignment

## Problem
The home.html template has redundant HTML structure (DOCTYPE, html, head, body tags) that conflicts with base.html when rendered, causing misalignment issues.

## Solution
Remove the redundant HTML structure from home.html and keep only the content that should be inside the body.

## Steps
- [x] 1. Analyze base.html and home.html to understand the conflict
- [x] 2. Fix home.html by removing redundant HTML structure
- [x] 3. Add home-page specific styles to static/css/style.css
- [x] 4. Test the fix (by verifying the code is correct)

