import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import axios from 'axios';

import { Media } from '../../types';
import { MovieSummary, toMedia } from '../../lib/movies';
import styles from '../../styles/Cards.module.scss';

const Cards = dynamic(import('./Cards'));
const FeatureCard = dynamic(import('./FeatureCards'));

interface ListProps {
  defaultCard?: boolean;
  heading: string;
  topList?: boolean;
  endpoint: string;
}

export default function List({
  defaultCard = true,
  heading,
  topList = false,
  endpoint
}: ListProps): React.ReactElement {
  const [media, setMedia] = useState<Media[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    axios.get<MovieSummary[]>(endpoint)
      .then(result => {
        setMedia(result.data.map(toMedia));
        setError(false);
      })
      .catch(() => setError(true));
  }, [endpoint]);

  return (
    <div className={styles.listContainer}>
      <strong className={styles.category}>{heading}</strong>
      {error && <p role='alert' className={styles.listError}>Không tải được danh sách phim.</p>}
      <div className={styles.cardRow}>
        {media.map((item, index) => {
          if (topList) {
            if (index < 10) return <FeatureCard key={item.id} index={index + 1} item={item} />;
            return null;
          }
          return <Cards key={item.id} defaultCard={defaultCard} item={item} />;
        })}
      </div>
    </div>
  );
}
