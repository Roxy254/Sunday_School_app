-- Add new tracking fields to attendance table
ALTER TABLE attendance
ADD COLUMN IF NOT EXISTS early boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS has_book boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS has_pen boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()); 