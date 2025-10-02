"use client";
import { useState } from "react";
import { Upload, X, Loader2 } from "lucide-react";
import { supabase } from "@/lib/supabase";

interface ImageUploadProps {
  value: string;
  onChange: (url: string) => void;
  bucket: "product-images" | "brand-assets";
  label?: string;
}

export default function ImageUpload({ value, onChange, bucket, label = "Image" }: ImageUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(value);

  const uploadImage = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB');
      return;
    }

    setUploading(true);
    try {
      const fileExt = file.name.split('.').pop();
      const fileName = `${Date.now()}-${Math.random().toString(36).substring(2)}.${fileExt}`;
      
      const { error: uploadError, data } = await supabase.storage
        .from(bucket)
        .upload(fileName, file, {
          cacheControl: '3600',
          upsert: false
        });

      if (uploadError) {
        console.error('Upload error:', uploadError);
        alert('Error uploading image: ' + uploadError.message);
        return;
      }

      const { data: { publicUrl } } = supabase.storage
        .from(bucket)
        .getPublicUrl(fileName);

      setPreview(publicUrl);
      onChange(publicUrl);
    } catch (error) {
      console.error('Error:', error);
      alert('Error uploading image');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-2">
      <label className="label">{label}</label>
      
      <div className="flex gap-2">
        <input
          type="url"
          className="input flex-1"
          placeholder="Image URL or upload file"
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setPreview(e.target.value);
          }}
        />
        
        <label className="btn btn-ghost relative cursor-pointer">
          <input
            type="file"
            className="hidden"
            accept="image/jpeg,image/jpg,image/png,image/webp,image/gif"
            onChange={uploadImage}
            disabled={uploading}
          />
          {uploading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Upload className="h-5 w-5" />
          )}
          <span className="ml-2">Upload</span>
        </label>
      </div>

      {preview && preview !== '/placeholder.svg' && (
        <div className="relative h-32 w-32 overflow-hidden rounded-xl border">
          <img src={preview} alt="Preview" className="w-full h-full object-cover" />
          <button
            type="button"
            className="absolute right-1 top-1 rounded-full bg-red-500 p-1 text-white hover:bg-red-600"
            onClick={() => {
              setPreview("");
              onChange("");
            }}
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      )}
      
      <p className="text-xs text-gray-500">
        Upload JPG, PNG, WebP or GIF (max 5MB) or paste an image URL
      </p>
    </div>
  );
}
