type RoutePlaceholderProps = {
  title: string;
  description: string;
};

export function RoutePlaceholder({ title, description }: RoutePlaceholderProps) {
  return (
    <section className="max-w-3xl">
      <h1 className="text-3xl font-semibold tracking-normal">{title}</h1>
      <p className="mt-3 text-base leading-7 text-muted-foreground">
        {description}
      </p>
    </section>
  );
}
