import type { FC } from "react";

const App: FC = () => {
  const message = import.meta.env.VITE_MESSAGE || 'Hello world!';

  return (
    <section>
      <p style={{ color: 'black' }}>{message}</p>
    </section>
  )
};

export default App;
