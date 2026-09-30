package com.project.movie_recommendation.mapper;

import com.project.movie_recommendation.dto.response.MovieDetailResponse;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.entity.Movie;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface MovieMapper {

    @Mapping(target = "posterUrl", source = "posterPath")
    @Mapping(target = "backdropUrl", source = "backdropPath")
    MovieDetailResponse toMovieDetailResponse(Movie movie);


    @Mapping(target = "posterUrl", source = "posterPath")
    @Mapping(target = "backdropUrl", source = "backdropPath")
    @Mapping(target = "voteAverage", expression = "java(movie.getTmdbVoteAverage() != null && movie.getTmdbVoteAverage() > 0 ? movie.getTmdbVoteAverage() : movie.getImdbRating())")
    MovieSummaryResponse toMovieSummaryResponse(Movie movie);
}
