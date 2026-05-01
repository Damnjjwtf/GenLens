import { redirect } from 'next/navigation';

export default function SignIn({
  searchParams,
}: {
  searchParams: { next?: string };
}) {
  const next = searchParams.next;
  const target = next ? `/?next=${encodeURIComponent(next)}#sign-in` : '/#sign-in';
  redirect(target);
}
