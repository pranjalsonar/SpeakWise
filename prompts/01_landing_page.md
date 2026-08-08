# SpeakWise - Sprint 1
## Feature 01 - Landing Page

# Project Context

You are an experienced Senior Frontend Engineer working on SpeakWise.

SpeakWise is an AI-powered public speaking coach for students.

The application helps students:
- Improve confidence
- Practice public speaking
- Expand vocabulary
- Receive AI feedback
- Learn new domains through guided speaking practice

The codebase is built using:

- React
- TypeScript
- Vite
- ESLint

Follow clean architecture and component-based design.

---

# Objective

Create a modern responsive landing page for SpeakWise.

The design should look professional and startup-quality.

The UI should be clean, minimal, and suitable for an AI product.

---

# Design Theme

Style:

- Modern
- Clean
- Professional
- White background
- Blue primary color
- Rounded cards
- Soft shadows
- Smooth spacing
- Mobile responsive

Do NOT use Bootstrap.

Use plain CSS.

---

# Folder Structure

Create components inside:

src/components/

Example:

components/

Navbar.tsx

Hero.tsx

FeatureCard.tsx

Features.tsx

Footer.tsx

---

# Components

## Navbar

Contains

- SpeakWise logo (text only)
- Home
- Features
- About
- Contact
- Get Started button

Navbar should remain clean and responsive.

---

## Hero Section

Contains

Large heading

"Master Public Speaking with AI"

Short paragraph explaining the platform.

Two buttons

Primary

Get Started

Secondary

Learn More

On the right side place a placeholder illustration using a styled div.

No external images.

---

## Features Section

Title

Why SpeakWise?

Four feature cards

Feature 1

Random Speaking Topics

Feature 2

AI Speech Analysis

Feature 3

Vocabulary Improvement

Feature 4

Confidence Tracking

Each card contains

- simple icon (emoji acceptable)
- title
- short description

---

## Footer

Contains

SpeakWise

Copyright

2026

Quick Links

Social placeholders

---

# Styling

Create reusable CSS.

Avoid inline styles.

Use Flexbox.

Use CSS variables for colors.

Use spacing consistently.

Cards should animate slightly on hover.

Buttons should have hover effects.

---

# Technical Requirements

Use

Functional Components

TypeScript

Props where appropriate

Reusable FeatureCard component

Do not duplicate code.

---

# Code Quality

Follow ESLint.

No warnings.

Readable variable names.

Proper folder organization.

Export components individually.

---

# Expected Folder Structure

src/

components/

Navbar.tsx

Hero.tsx

FeatureCard.tsx

Features.tsx

Footer.tsx

App.tsx

index.css

---

# Acceptance Criteria

The application should

Run successfully using

npm run dev

Be responsive

Contain reusable components

Have clean code

No TypeScript errors

No ESLint errors

Ready for future routing.
