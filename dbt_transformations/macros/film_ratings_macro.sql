{% macro generate_film_ratings() %}


WITH films_with_ratings AS (
    SELECT 
        film_id,
        title,
        release_date,
        price,
        rating,
        user_rating,
        {{generate_ratings_macro()}}
    FROM {{ ref('films') }}
),

films_with_actors as (
    SELECT
        f.film_id,
        f.title,
        string_agg(a.actor_name, ',') AS actors
    FROM {{ ref('films') }} f
    LEFT JOIN {{ ref('film_actors') }} fa ON f.film_id = fa.film_id
    LEFT JOIN {{ ref('actors') }}  a ON fa.actor_id = a.actor_id
    GROUP BY f.film_id, f.title
)


SELECT fwf.*, fwa.actors
FROM
    films_with_ratings fwf
    LEFT JOIN films_with_actors fwa ON fwf.film_id = fwa.film_id

{% endmacro %}