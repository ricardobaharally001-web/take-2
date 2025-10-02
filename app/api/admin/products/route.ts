import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function GET(request: NextRequest) {
  try {
    const { data, error } = await supabase
      .from('products')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ data });
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate required fields
    if (!body.name || !body.price_cents || body.stock === undefined) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }

    // Sanitize and validate input
    const productData = {
      name: body.name.trim(),
      description: body.description?.trim() || null,
      price_cents: Math.max(0, parseInt(body.price_cents)),
      stock: Math.max(0, parseInt(body.stock)),
      category_id: body.category_id || null,
      image_url: body.image_url?.trim() || null,
      is_active: Boolean(body.is_active)
    };

    const { data, error } = await supabase
      .from('products')
      .insert([productData])
      .select()
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ data }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();
    const { id, ...updateData } = body;

    if (!id) {
      return NextResponse.json({ error: 'Product ID is required' }, { status: 400 });
    }

    // Sanitize and validate input
    const sanitizedData: any = {};
    if (updateData.name) sanitizedData.name = updateData.name.trim();
    if (updateData.description !== undefined) sanitizedData.description = updateData.description?.trim() || null;
    if (updateData.price_cents !== undefined) sanitizedData.price_cents = Math.max(0, parseInt(updateData.price_cents));
    if (updateData.stock !== undefined) sanitizedData.stock = Math.max(0, parseInt(updateData.stock));
    if (updateData.category_id !== undefined) sanitizedData.category_id = updateData.category_id || null;
    if (updateData.image_url !== undefined) sanitizedData.image_url = updateData.image_url?.trim() || null;
    if (updateData.is_active !== undefined) sanitizedData.is_active = Boolean(updateData.is_active);

    const { data, error } = await supabase
      .from('products')
      .update(sanitizedData)
      .eq('id', id)
      .select()
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ data });
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
      return NextResponse.json({ error: 'Product ID is required' }, { status: 400 });
    }

    const { error } = await supabase
      .from('products')
      .delete()
      .eq('id', id);

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ message: 'Product deleted successfully' });
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
