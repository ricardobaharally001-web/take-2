import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function GET(request: NextRequest) {
  try {
    const { data, error } = await supabase
      .from('site_settings')
      .select('*');

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    // Convert array to object
    const settings: Record<string, any> = {};
    (data || []).forEach((row: any) => {
      settings[row.key] = row.value;
    });

    return NextResponse.json({ data: settings });
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();
    
    if (!body || typeof body !== 'object') {
      return NextResponse.json({ error: 'Invalid settings data' }, { status: 400 });
    }

    // Validate and sanitize settings
    const allowedKeys = [
      'business_name',
      'logo_url', 
      'theme',
      'whatsapp_number',
      'stock_display'
    ];

    const sanitizedSettings: Record<string, any> = {};
    
    for (const [key, value] of Object.entries(body)) {
      if (!allowedKeys.includes(key)) {
        continue; // Skip unknown keys
      }

      // Sanitize based on key type
      switch (key) {
        case 'business_name':
          sanitizedSettings[key] = typeof value === 'string' ? value.trim().slice(0, 100) : value;
          break;
        case 'logo_url':
          sanitizedSettings[key] = typeof value === 'string' ? value.trim().slice(0, 500) : value;
          break;
        case 'theme':
          sanitizedSettings[key] = ['light', 'dark', 'system'].includes(value as string) ? value : 'system';
          break;
        case 'whatsapp_number':
          // Remove all non-digit characters and validate
          const cleanNumber = typeof value === 'string' ? value.replace(/\D/g, '') : '';
          sanitizedSettings[key] = cleanNumber.length >= 10 ? cleanNumber : (value as string);
          break;
        case 'stock_display':
          sanitizedSettings[key] = Boolean(value);
          break;
        default:
          sanitizedSettings[key] = value;
      }
    }

    // Update settings in batch
    const updates = Object.entries(sanitizedSettings).map(([key, value]) => ({
      key,
      value
    }));

    const { error } = await supabase
      .from('site_settings')
      .upsert(updates, { onConflict: 'key' });

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ message: 'Settings updated successfully' });
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
