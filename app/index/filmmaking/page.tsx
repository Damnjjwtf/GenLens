import { renderVerticalIndex, generateVerticalMetadata } from '@/components/IndexVerticalPage'

export const dynamic = 'force-dynamic'

export async function generateMetadata() {
  return generateVerticalMetadata('filmmaking')
}

export default async function Page() {
  return renderVerticalIndex('filmmaking')
}
