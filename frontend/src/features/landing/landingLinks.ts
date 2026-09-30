/** In-page anchors for the landing nav and footer links. */
export const landingHref = (link: string): string => {
  switch (link) {
    case 'Home':
      return '#top'
    case 'Features':
      return '#features'
    case 'About':
      return '#about'
    default:
      return '#contact'
  }
}
