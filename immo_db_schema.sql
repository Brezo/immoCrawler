--
-- PostgreSQL database dump
--

-- Dumped from database version 14.2
-- Dumped by pg_dump version 14.2

-- Started on 2023-03-03 22:05:30

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 211 (class 1255 OID 32794)
-- Name: update_timestamp(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$BEGIN
    NEW.change_tstmp := current_timestamp;
    RETURN NEW;
END$$;


ALTER FUNCTION public.update_timestamp() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 209 (class 1259 OID 16396)
-- Name: crawled_immo; Type: TABLE; Schema: public; Owner: immo_crawler
--

CREATE TABLE public.crawled_immo (
    provider character(10) NOT NULL,
    id character(36) NOT NULL,
    has_garden boolean,
    has_terrace boolean,
    has_loggia boolean,
    has_balcony boolean,
    status character(20) NOT NULL,
    rooms numeric(2,1) NOT NULL,
    surface numeric(5,2) NOT NULL,
    rent numeric(6,2) NOT NULL,
    self_funding numeric(8,2) NOT NULL,
    postcode character(4) NOT NULL,
    street character(50) NOT NULL,
    city character(40) NOT NULL,
    creation_tstmp timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    change_tstmp timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    detail_url character(250) NOT NULL
);


ALTER TABLE public.crawled_immo OWNER TO immo_crawler;

--
-- TOC entry 210 (class 1259 OID 49185)
-- Name: available_immo; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.available_immo AS
 SELECT crawled_immo.provider,
    crawled_immo.id,
    crawled_immo.has_garden,
    crawled_immo.has_terrace,
    crawled_immo.has_loggia,
    crawled_immo.has_balcony,
    crawled_immo.status,
    crawled_immo.rooms,
    crawled_immo.surface,
    crawled_immo.rent,
    crawled_immo.self_funding,
    crawled_immo.postcode,
    crawled_immo.street,
    crawled_immo.city,
    crawled_immo.creation_tstmp,
    crawled_immo.change_tstmp,
    crawled_immo.detail_url
   FROM public.crawled_immo
  WHERE (crawled_immo.status = ANY (ARRAY['available'::bpchar, ''::bpchar, NULL::bpchar]));


ALTER TABLE public.available_immo OWNER TO postgres;

--
-- TOC entry 3171 (class 2606 OID 40988)
-- Name: crawled_immo crawled_immo_pkey; Type: CONSTRAINT; Schema: public; Owner: immo_crawler
--

ALTER TABLE ONLY public.crawled_immo
    ADD CONSTRAINT crawled_immo_pkey PRIMARY KEY (provider, id);


--
-- TOC entry 3172 (class 2620 OID 32795)
-- Name: crawled_immo on_update; Type: TRIGGER; Schema: public; Owner: immo_crawler
--

CREATE TRIGGER on_update BEFORE UPDATE ON public.crawled_immo FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- TOC entry 3318 (class 0 OID 0)
-- Dependencies: 3
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA public TO web_anon;


--
-- TOC entry 3319 (class 0 OID 0)
-- Dependencies: 209
-- Name: TABLE crawled_immo; Type: ACL; Schema: public; Owner: immo_crawler
--

GRANT SELECT ON TABLE public.crawled_immo TO web_anon;


--
-- TOC entry 3320 (class 0 OID 0)
-- Dependencies: 210
-- Name: TABLE available_immo; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT ON TABLE public.available_immo TO web_anon;


-- Completed on 2023-03-03 22:05:31

--
-- PostgreSQL database dump complete
--

