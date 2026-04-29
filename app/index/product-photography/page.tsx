import { renderVerticalIndex, generateVerticalMetadata } from '@/components/IndexVerticalPage'

export const revalidate = 3600

export async function generateMetadata() {
  return generateVerticalMetadata('product_photography')
}

export default async function Page() {
  return renderVerticalIndex('product_photography')
}
