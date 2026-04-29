{% set film_title = 'Dunkirk' %}

select * from {{'films'}} where title = '{{film_title}}'