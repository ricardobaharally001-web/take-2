# Security Setup Guide

This guide will help you set up the secure version of your restaurant website.

## 🔒 Security Improvements Made

### 1. **Authentication System**
- ✅ Replaced simple password with Supabase Auth
- ✅ Email-based login with secure password reset
- ✅ JWT token validation
- ✅ Session management

### 2. **Database Security**
- ✅ Row Level Security (RLS) policies
- ✅ Admin-only access to sensitive operations
- ✅ Input validation and sanitization
- ✅ Proper error handling

### 3. **API Security**
- ✅ Server-side API routes for admin operations
- ✅ Input validation and sanitization
- ✅ Rate limiting
- ✅ CSRF protection

### 4. **Environment Security**
- ✅ Service role key for server operations
- ✅ Secure environment variable handling
- ✅ No client-side sensitive data exposure

## 🚀 Setup Instructions

### Step 1: Database Setup

1. **Run the secure SQL script:**
   ```sql
   -- Copy and paste the contents of supabase-secure.sql into your Supabase SQL Editor
   ```

2. **Create admin user:**
   ```sql
   -- Replace 'your-email@example.com' with your actual email
   SELECT public.create_admin_user('your-email@example.com');
   ```

3. **Set up storage buckets:**
   - Go to Storage in your Supabase dashboard
   - Create two buckets: `product-images` and `brand-assets`
   - Make both buckets PUBLIC
   - Run the storage policies from the SQL script

### Step 2: Environment Variables

Create a `.env.local` file in your project root:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Service Role Key (for server-side operations)
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Optional: Custom domain for production
NEXT_PUBLIC_SITE_URL=https://yourdomain.com
```

### Step 3: Install Dependencies

```bash
npm install
```

### Step 4: Run the Application

```bash
npm run dev
```

## 🔐 Admin Access

1. **First-time setup:**
   - Go to `/admin`
   - Use the email you created the admin user with
   - Click "Forgot your password?" to set your password
   - Check your email for the reset link

2. **Login:**
   - Use your email and password to access the admin panel
   - All admin operations are now secure and require authentication

## 🛡️ Security Features

### Rate Limiting
- **Public routes:** 100 requests per 15 minutes
- **Admin routes:** 50 requests per 15 minutes
- **Automatic blocking** of excessive requests

### Input Validation
- **Server-side validation** for all inputs
- **SQL injection protection** via parameterized queries
- **XSS protection** via input sanitization
- **File upload validation** for images

### Authentication
- **JWT-based authentication** with Supabase
- **Secure password requirements:**
  - Minimum 8 characters
  - Uppercase and lowercase letters
  - Numbers and special characters
- **Password reset** via email
- **Session management** with automatic refresh

### Database Security
- **Row Level Security (RLS)** policies
- **Admin-only access** to sensitive operations
- **Public read access** to products and categories
- **Audit logging** for admin actions

## 🚨 Security Checklist

Before going live, ensure:

- [ ] All environment variables are set correctly
- [ ] Admin user is created in the database
- [ ] Storage buckets are configured
- [ ] HTTPS is enabled in production
- [ ] Domain is configured in Supabase
- [ ] Rate limiting is working
- [ ] All admin operations require authentication
- [ ] Input validation is working
- [ ] Error messages don't expose sensitive information

## 🔧 Troubleshooting

### Common Issues:

1. **"Invalid reset link" error:**
   - Check that your domain is configured in Supabase
   - Ensure the redirect URL matches your domain

2. **"Rate limited" error:**
   - Wait 15 minutes or restart the server
   - Check if you're making too many requests

3. **"Authentication failed" error:**
   - Verify your email is in the admin_users table
   - Check Supabase Auth configuration

4. **"Permission denied" error:**
   - Ensure RLS policies are set up correctly
   - Check that you're logged in as an admin

## 📞 Support

If you encounter any issues:

1. Check the browser console for errors
2. Check the server logs
3. Verify all environment variables are set
4. Ensure the database is properly configured

## 🎯 Next Steps

After setting up security:

1. **Test all admin functions** to ensure they work
2. **Set up monitoring** for security events
3. **Regular security updates** of dependencies
4. **Backup your database** regularly
5. **Monitor rate limiting** and adjust if needed

Your restaurant website is now production-ready with enterprise-level security! 🎉
