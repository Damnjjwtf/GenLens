import { Suspense } from 'react';
import InviteFlow from './invite-flow';

export const dynamic = 'force-dynamic';

export default function InvitePage() {
  return (
    <Suspense fallback={null}>
      <InviteFlow />
    </Suspense>
  );
}
