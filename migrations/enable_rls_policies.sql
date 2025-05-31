-- Enable RLS
ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;

-- Create policy to enable all operations
CREATE POLICY "Enable all operations for authenticated users"
ON attendance
FOR ALL
TO authenticated, anon
USING (true)
WITH CHECK (true); 