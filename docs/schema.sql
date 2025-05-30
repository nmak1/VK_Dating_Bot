-- DROP SCHEMA public;

CREATE SCHEMA public AUTHORIZATION pg_database_owner;

COMMENT ON SCHEMA public IS 'standard public schema';
-- public.blacklist определение

-- Drop table

-- DROP TABLE public.blacklist;

CREATE TABLE public.blacklist (
	user_id int8 NOT NULL, -- ID of the user who created the ban
	banned_id int8 NOT NULL, -- ID of the banned user
	CONSTRAINT blacklist_pkey PRIMARY KEY (user_id, banned_id)
);
CREATE INDEX idx_blacklist_banned_id ON public.blacklist USING btree (banned_id);
CREATE INDEX idx_blacklist_user_id ON public.blacklist USING btree (user_id);
COMMENT ON TABLE public.blacklist IS 'Table for storing user blacklist in dating bot';

-- Column comments

COMMENT ON COLUMN public.blacklist.user_id IS 'ID of the user who created the ban';
COMMENT ON COLUMN public.blacklist.banned_id IS 'ID of the banned user';


-- public.favorites определение

-- Drop table

-- DROP TABLE public.favorites;

CREATE TABLE public.favorites (
	user_id int8 NOT NULL, -- ID of the user who added to favorites
	favorite_id int8 NOT NULL, -- ID of the favorited user
	added_at timestamp NULL, -- Timestamp when the user was added to favorites
	CONSTRAINT favorites_pkey PRIMARY KEY (user_id, favorite_id)
);
CREATE INDEX idx_favorites_favorite_id ON public.favorites USING btree (favorite_id);
CREATE INDEX idx_favorites_user_id ON public.favorites USING btree (user_id);
COMMENT ON TABLE public.favorites IS 'Table for storing user favorites in dating bot';

-- Column comments

COMMENT ON COLUMN public.favorites.user_id IS 'ID of the user who added to favorites';
COMMENT ON COLUMN public.favorites.favorite_id IS 'ID of the favorited user';
COMMENT ON COLUMN public.favorites.added_at IS 'Timestamp when the user was added to favorites';


-- public.photo_likes определение

-- Drop table

-- DROP TABLE public.photo_likes;

CREATE TABLE public.photo_likes (
	user_id int8 NOT NULL, -- ID of the user who liked the photo
	photo_id text NOT NULL, -- ID of the photo that was liked
	liked bool NULL, -- Boolean flag indicating like status
	CONSTRAINT photo_likes_pkey PRIMARY KEY (user_id, photo_id)
);
CREATE INDEX idx_photo_likes_photo_id ON public.photo_likes USING btree (photo_id);
CREATE INDEX idx_photo_likes_user_id ON public.photo_likes USING btree (user_id);
COMMENT ON TABLE public.photo_likes IS 'Table for storing photo likes in dating bot';

-- Column comments

COMMENT ON COLUMN public.photo_likes.user_id IS 'ID of the user who liked the photo';
COMMENT ON COLUMN public.photo_likes.photo_id IS 'ID of the photo that was liked';
COMMENT ON COLUMN public.photo_likes.liked IS 'Boolean flag indicating like status';