import { renderVerticalIndex, generateVerticalMetadata } from '@/components/IndexVerticalPage'

export const revalidate = 3600

export async function generateMetadata() {
  return generateVerticalMetadata('digital_humans')
}

export default async function Page() {
  return renderVerticalIndex('digital_humans')
}
