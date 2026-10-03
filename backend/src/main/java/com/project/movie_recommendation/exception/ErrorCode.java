package com.project.movie_recommendation.exception;

public enum ErrorCode {
    UNCATEGORIZED_EXCEPTION(9999, "Uncategorized error"),
    INVALID_KEY(1001,"INVALID_KEY"),
    USER_EXISTED(1002, "User existed"),
    INVALID_PASSWORD(1003, "Password must be at least 8 characters"),
    USER_NOT_EXISTED(1004, "User not existed"),
    UNAUTHENTICATED(1005, "Unauthenticated"),
    EMAIL_INVALID(1006, "Invalid email format"),
    EMAIL_IS_REQUIRED(1007, "Email must not be blank"),
    UNAUTHORIZED_ACCESS(1008, "You do not have permission to access this resource"),

    MOVIE_NOT_FOUND(2001, "Movie not found"),
    TRAILER_NOT_FOUND(2002, "Trailer not found for this movie"),

    WATCHLIST_NOT_FOUND(3001, "Watchlist not found"),
    MOVIE_ALREADY_IN_WATCHLIST(3002, "Movie is already in watchlist"),
    MOVIE_NOT_IN_WATCHLIST(3003, "Movie is not in watchlist"),

    WATCH_HISTORY_NOT_FOUND(4001, "Watch history record not found")
    ;

    private int code;
    private String message;

    ErrorCode(int code, String message) {
        this.code = code;
        this.message = message;
    }

    public int getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }
}

