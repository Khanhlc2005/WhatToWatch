package com.project.movie_recommendation.mapper;

import com.project.movie_recommendation.dto.response.MovieDetailResponse;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.entity.Movie;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface MovieMapper {
    MovieDetailResponse toMovieDetailResponse(Movie movie);
    MovieSummaryResponse toMovieSummaryResponse(Movie movie);
}