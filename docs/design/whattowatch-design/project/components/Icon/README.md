One stroked icon set (24px grid, 1.5px stroke, round caps, Lucide style) that replaces `react-icons` across the app.

- Props: `name` (one of the names shown), `size` (18 default inside buttons, 20 in the navbar, 22 for float buttons), `filled` (heart, star and play only), `label` (gives it `role="img"`; leave it out for decorative icons).
- Icons take `currentColor`, so colour them through their parent's text colour.
- Use a filled icon only to show a state that is on (favourited, rated). Production can use `lucide-react` with the same names.
