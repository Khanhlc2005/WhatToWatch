package com.project.movie_recommendation.mapper;

import com.project.movie_recommendation.dto.response.MovieDetailResponse;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.MovieCast;
import com.project.movie_recommendation.entity.MovieCrew;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface MovieMapper {

    MovieDetailResponse toMovieDetailResponse(Movie movie);

    @Mapping(target = "personId", source = "person.id")
    @Mapping(target = "name", source = "person.name")
    MovieDetailResponse.CastResponse toCastResponse(MovieCast movieCast);

    @Mapping(target = "personId", source = "person.id")
    @Mapping(target = "name", source = "person.name")
    MovieDetailResponse.CrewResponse toCrewResponse(MovieCrew movieCrew);


    @Mapping(target = "posterUrl", source = "posterPath")
    @Mapping(target = "voteAverage", expression = "java(movie.getTmdbVoteAverage() != null && movie.getTmdbVoteAverage() > 0 ? movie.getTmdbVoteAverage() : movie.getImdbRating())")
    MovieSummaryResponse toMovieSummaryResponse(Movie movie);
}