package com.project.movie_recommendation.configuration;

import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.repository.MovieRepository;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@Configuration
public class DemoMovieData {
    @Bean
    @ConditionalOnProperty(name = "app.demo-data.enabled", havingValue = "true")
    ApplicationRunner seedDemoMovies(MovieRepository movies) {
        return args -> {
            Map<String, String> backdrops = Map.of(
                "Interstellar", "https://image.tmdb.org/t/p/original/8sNiAPPYU14PUepFNeSNGUTiHW.jpg",
                "The Godfather", "https://image.tmdb.org/t/p/original/tSPT36ZKlP2WVHJLM4cQPLSzv3b.jpg",
                "Fight Club", "https://image.tmdb.org/t/p/original/c6OLXfKAk5BKeR6broC8pYiCquX.jpg"
            );
            if (movies.count() > 0) {
                backdrops.forEach((title, url) -> movies.findFirstByTitle(title).ifPresent(movie -> {
                    if (movie.getBackdropUrl() == null || movie.getBackdropUrl().isBlank()) {
                        movie.setBackdropUrl(url);
                        movies.save(movie);
                    }
                }));
                return;
            }
            movies.saveAll(List.of(
                Movie.builder()
                    .title("Interstellar")
                    .overview("A team of explorers travels beyond this galaxy to discover whether mankind has a future among the stars.")
                    .posterUrl("https://image.tmdb.org/t/p/w500/yQvGrMoipbRoddT0ZR8tPoR7NfX.jpg")
                    .backdropUrl(backdrops.get("Interstellar"))
                    .releaseDate(LocalDate.of(2014, 11, 5)).voteAverage(8.5).runtime(169)
                    .genres("Adventure, Drama, Science Fiction")
                    .cast("Matthew McConaughey, Anne Hathaway, Jessica Chastain")
                    .trailerYoutubeKey("zSWdZVtXT7E").build(),
                Movie.builder()
                    .title("The Godfather")
                    .overview("The aging patriarch of an organized crime dynasty transfers control of his empire to his reluctant son.")
                    .posterUrl("https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg")
                    .backdropUrl(backdrops.get("The Godfather"))
                    .releaseDate(LocalDate.of(1972, 3, 14)).voteAverage(8.7).runtime(175)
                    .genres("Crime, Drama").cast("Marlon Brando, Al Pacino, James Caan")
                    .trailerYoutubeKey("Ew9ngL1GZvs").build(),
                Movie.builder()
                    .title("Fight Club")
                    .overview("An insomniac office worker and a soap maker form an underground fight club.")
                    .posterUrl("https://image.tmdb.org/t/p/w500/jSziioSwPVrOy9Yow3XhWIBDjq1.jpg")
                    .backdropUrl(backdrops.get("Fight Club"))
                    .releaseDate(LocalDate.of(1999, 10, 15)).voteAverage(8.4).runtime(139)
                    .genres("Drama, Thriller").cast("Edward Norton, Brad Pitt, Helena Bonham Carter")
                    .trailerYoutubeKey("BdJKm16Co6M").build()
            ));
        };
    }
}
