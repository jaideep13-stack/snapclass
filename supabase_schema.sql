-- SnapClass Supabase Schema
-- Run this in your Supabase SQL editor to set up the database

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ─── Profiles ────────────────────────────────────────────────────────────────
-- Auto-created when a user signs up via Supabase Auth trigger
create table if not exists profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text,
    full_name text,
    role text check (role in ('teacher', 'student')),
    face_encoding float8[],        -- 128-dim face_recognition vector
    voice_encoding float8[],       -- resemblyzer embedding
    created_at timestamptz default now()
);

-- Trigger: auto-create profile on new user signup
create or replace function handle_new_user()
returns trigger as $$
begin
    insert into public.profiles (id, email, full_name, role)
    values (
        new.id,
        new.email,
        new.raw_user_meta_data->>'full_name',
        new.raw_user_meta_data->>'role'
    );
    return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure handle_new_user();


-- ─── Classes ─────────────────────────────────────────────────────────────────
create table if not exists classes (
    id uuid primary key default uuid_generate_v4(),
    teacher_id uuid references profiles(id) on delete cascade,
    class_name text not null,
    subject text,
    join_code text unique not null,
    is_active boolean default true,
    created_at timestamptz default now()
);


-- ─── Enrollments ─────────────────────────────────────────────────────────────
create table if not exists enrollments (
    id uuid primary key default uuid_generate_v4(),
    class_id uuid references classes(id) on delete cascade,
    student_id uuid references profiles(id) on delete cascade,
    enrolled_at timestamptz default now(),
    unique(class_id, student_id)
);


-- ─── Attendance Sessions ──────────────────────────────────────────────────────
create table if not exists attendance_sessions (
    id uuid primary key default uuid_generate_v4(),
    class_id uuid references classes(id) on delete cascade,
    teacher_id uuid references profiles(id),
    session_date date not null,
    is_active boolean default true,
    created_at timestamptz default now()
);


-- ─── Attendance Records ───────────────────────────────────────────────────────
create table if not exists attendance_records (
    id uuid primary key default uuid_generate_v4(),
    session_id uuid references attendance_sessions(id) on delete cascade,
    student_id uuid references profiles(id) on delete cascade,
    class_id uuid references classes(id) on delete cascade,
    method text check (method in ('face', 'voice', 'manual')),
    marked_at timestamptz default now(),
    unique(session_id, student_id)
);


-- ─── Row Level Security ───────────────────────────────────────────────────────
alter table profiles enable row level security;
alter table classes enable row level security;
alter table enrollments enable row level security;
alter table attendance_sessions enable row level security;
alter table attendance_records enable row level security;

-- Profiles: users can read all profiles, update only their own
create policy "profiles_select" on profiles for select using (true);
create policy "profiles_update" on profiles for update using (auth.uid() = id);

-- Classes: teachers manage their own, everyone can read
create policy "classes_select" on classes for select using (true);
create policy "classes_insert" on classes for insert with check (auth.uid() = teacher_id);
create policy "classes_update" on classes for update using (auth.uid() = teacher_id);
create policy "classes_delete" on classes for delete using (auth.uid() = teacher_id);

-- Enrollments: students manage their own, teachers read theirs
create policy "enrollments_select" on enrollments for select using (true);
create policy "enrollments_insert" on enrollments for insert with check (auth.uid() = student_id);
create policy "enrollments_delete" on enrollments for delete using (auth.uid() = student_id);

-- Sessions: teachers manage, all read
create policy "sessions_select" on attendance_sessions for select using (true);
create policy "sessions_insert" on attendance_sessions for insert with check (auth.uid() = teacher_id);
create policy "sessions_update" on attendance_sessions for update using (auth.uid() = teacher_id);

-- Records: authenticated users can insert/read
create policy "records_select" on attendance_records for select using (true);
create policy "records_insert" on attendance_records for insert with check (auth.uid() is not null);
