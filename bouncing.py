import pygame
import random
import math





class Particle:
    def __init__(self, pos: (int, int), size: int, angle: float, speed):
        self._x, self._y = pos
        self._size = size
        self._color = (0, 0, 255)
        self._thickness = 1
        # Attributes for movement.
        self._speed = speed
        self._angle = angle
    
    def display(self, surface: pygame.surface):
        """Display this particle using pygame.draw.circle and a provided surface."""
        pygame.draw.circle(
            surface, 
            self._color, 
            (math.floor(self._x), math.floor(self._y)), 
            self._size, 
            self._thickness
        )
    
    def move(self) -> None:
        self._x += math.cos(self._angle) * self._speed
        self._y -= math.sin(self._angle) * self._speed
    
    def bounce(self, dimensions: (int, int)) -> None:
        width, height = dimensions
        
        if not self._size <= self._x <= width - self._size:
            self._angle = math.pi - self._angle
        
        if not self._size <= self._y <= height - self._size:
            self._angle = - self._angle
        






class Simulation:
    """Parent class for the simulation in the tutorial."""
    def __init__(self):
        self._width, self._height = (800, 800)
        self._running = True
        self._surface = pygame.display.set_mode((self._width, self._height))
        pygame.display.set_caption('Tutorial 1')
        self._surface.fill((255, 255, 255)) # Makes the background white.

        # Create 12 random particles.
        self._particles = []
        for _ in range(12):
            size = random.randint(10, 20) # size = radius. Something between 10 and 20 pixels.
            # Width - size and height - size are to ensure the full circle is visible on the screen.
            x, y = random.randint(size, self._width - size), random.randint(size, self._height - size)
            angle = random.uniform(0, 2 * math.pi)
            speed = random.random() * 0.5
            self._particles.append(Particle((x, y), size, angle, speed))
    
    def run(self) -> None:
        """Run the simulation."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
            
            self._redraw_frame()
    
    def _redraw_frame(self) -> None:
        """Redraw the frame."""
        self._surface.fill((255, 255, 255))
        self._draw_particles()
        pygame.display.flip()
    
    def _draw_particles(self) -> None:
        """Draw all the particles."""
        for particle in self._particles:
            particle.move()
            particle.bounce((self._width, self._height))
            particle.display(self._surface)

    # def _draw_circle(self) -> None:
    #     """Draw a pygame circle.

    #     pygame.draw.circle(surface, color: tuple, center: [] or tuple, radius: int or float, width: int (line thickness))
    #     If width is 0 (default), the circle is filled.
    #     <0 and nothing is drawn, >0 and this argument changes line thickness.
    #     """

    #     pygame.draw.circle(self._surface, (0, 0, 255), (150, 50), 15, 1)

if __name__ == '__main__':
    Simulation().run()