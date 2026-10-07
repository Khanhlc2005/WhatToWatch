import { NextApiRequest, NextApiResponse } from 'next';
import { allowMethod, sendError } from '../../../../lib/api';
import { backendRequest } from '../../../../lib/backend';
import { MovieDetail, Trailer } from '../../../../lib/movies';
import { resolveTrailer } from '../../../../lib/trailerLookup';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (!allowMethod(req, res, 'GET')) return;
  const id = req.query.id;
  if (typeof id !== 'string' || !/^[1-9][0-9]*$/.test(id) || !Number.isSafeInteger(Number(id))) {
    res.status(400).json({ message: 'ID phim không hợp lệ' });
    return;
  }
  try {
    const movie = await backendRequest<MovieDetail>('/movies/' + id);
    const trailerKey = await resolveTrailer(movie);
    if (!trailerKey) {
      res.status(404).json({ message: 'Chưa tìm được trailer phù hợp cho phim này' });
      return;
    }
    const trailer: Trailer = { trailerKey, embedUrl: `https://www.youtube.com/embed/${trailerKey}` };
    res.status(200).json(trailer);
  } catch (error) {
    sendError(res, error);
  }
}
