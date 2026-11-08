import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const articles = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/articles' }),
  schema: z.object({
    title: z.string().min(1),
    slug: z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'lowercase letters, digits, hyphens only'),
    category: z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'lowercase letters, digits, hyphens only'),
    tags: z.array(z.string()).default([]),
    date: z.coerce.date(),
    published: z.boolean().default(false),
    hero: z.string().optional(),
    layoutVariant: z.enum(['classic-serif', 'modern-sans', 'photo-essay']).default('classic-serif'),
    excerpt: z.string().optional(),
    description: z.string().max(180).optional(),
  }),
});

export const collections = { articles };
