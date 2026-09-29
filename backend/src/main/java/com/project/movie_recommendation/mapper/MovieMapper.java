package com.project.movie_recommendation.mapper;

import com.project.movie_recommendation.dto.response.MovieDetailResponse;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.entity.Movie;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface MovieMapper {

    MovieDetailResponse toMovieDetailResponse(Movie movie);


    @Mapping(target = "posterUrl", source = "posterPath")
    @Mapping(target = "voteAverage", source = "tmdbVoteAverage")
    MovieSummaryResponse toMovieSummaryResponse(Movie movie);
}