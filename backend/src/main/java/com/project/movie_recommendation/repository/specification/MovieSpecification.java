package com.project.movie_recommendation.repository.specification;

import com.project.movie_recommendation.dto.request.MovieFilterRequest;
import com.project.movie_recommendation.entity.Genre;
import com.project.movie_recommendation.entity.Movie;
import jakarta.persistence.criteria.Join;
import jakarta.persistence.criteria.Predicate;
import org.springframework.data.jpa.domain.Specification;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class MovieSpecification {

    public static Specification<Movie> filterMovies(MovieFilterRequest request) {
        return (root, query, criteriaBuilder) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (Long.class != query.getResultType()) {
                query.distinct(true);
            }

            if (request.getGenreIds() != null && !request.getGenreIds().isEmpty()) {
                Join<Movie, Genre> genreJoin = root.join("genres");
                predicates.add(genreJoin.get("id").in(request.getGenreIds()));
            }

            if (request.getYearFrom() != null) {
                LocalDate startOfYear = LocalDate.of(request.getYearFrom(), 1, 1);
                predicates.add(criteriaBuilder.greaterThanOrEqualTo(root.get("releaseDate"), startOfYear));
            }
            if (request.getYearTo() != null) {
                LocalDate endOfYear = LocalDate.of(request.getYearTo(), 12, 31);
                predicates.add(criteriaBuilder.lessThanOrEqualTo(root.get("releaseDate"), endOfYear));
            }

            if (request.getMinRating() != null) {
                predicates.add(criteriaBuilder.greaterThanOrEqualTo(root.get("tmdbVoteAverage"), request.getMinRating()));
            }
            if (request.getMaxRating() != null) {
                predicates.add(criteriaBuilder.lessThanOrEqualTo(root.get("tmdbVoteAverage"), request.getMaxRating()));
            }

            if (request.getLanguage() != null && !request.getLanguage().isBlank()) {
                predicates.add(criteriaBuilder.equal(root.get("originalLanguage"), request.getLanguage()));
            }

            if (request.getMinRuntime() != null) {
                predicates.add(criteriaBuilder.greaterThanOrEqualTo(root.get("runtimeMinutes"), request.getMinRuntime()));
            }
            if (request.getMaxRuntime() != null) {
                predicates.add(criteriaBuilder.lessThanOrEqualTo(root.get("runtimeMinutes"), request.getMaxRuntime()));
            }

            return criteriaBuilder.and(predicates.toArray(new Predicate[0]));
        };
    }
}