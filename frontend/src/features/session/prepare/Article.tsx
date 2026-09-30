import type { ArticleSection } from '@/core/types'
import './Article.css'

/** Reading material: H2 sections, Literata paragraphs, pull-quotes and the Key points box. */
interface ArticleProps {
  sections: ArticleSection[]
  keyPoints: string[]
  /** A−/A+ step (−1 … +2). Each step changes the paragraph size by 2px. */
  textStep: number
}

export function Article({ sections, keyPoints, textStep }: ArticleProps) {
  return (
    <div className="article" data-text-step={textStep}>
      {sections.map((section) => (
        <section key={section.heading} className="article__section">
          <h2 className="article__heading">{section.heading}</h2>
          {section.paragraphs.map((paragraph, i) => (
            <p key={i} className="article__paragraph">
              {paragraph}
            </p>
          ))}
          {section.pullQuote && (
            <blockquote className="article__quote">{section.pullQuote}</blockquote>
          )}
          {section.showKeyPoints && (
            <aside className="article__keys" aria-labelledby="article-keys-title">
              <p id="article-keys-title" className="article__keys-title">
                Key points
              </p>
              <ol className="article__keys-list">
                {keyPoints.map((point, i) => (
                  <li key={point} className="article__key">
                    <span className="article__key-num">{i + 1}</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ol>
            </aside>
          )}
        </section>
      ))}
    </div>
  )
}
